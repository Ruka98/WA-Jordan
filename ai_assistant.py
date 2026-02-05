import os
import glob
import logging
import sys
import fnmatch
import re
import datetime
import tempfile
import numpy as np

# Data analysis imports
try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg') # Non-interactive backend
    import matplotlib.pyplot as plt
    import rasterio
except ImportError:
    pd = None
    plt = None
    rasterio = None

# Try to import llama_cpp, handle if missing
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# Import configuration from wa_config
# Adjust path to ensure import works if run from root or elsewhere
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from wa_config import dataset_config, file_patterns
except ImportError:
    # Fallback if running in isolation without wa_config available
    dataset_config = {}
    file_patterns = {}

class AIHandler:
    def __init__(self):
        self.llm = None
        self.model_path = None
        self.logger = logging.getLogger("AIAssistant")

    def load_model(self, model_path):
        if Llama is None:
            return False, "llama-cpp-python library not installed."

        try:
            if not os.path.exists(model_path):
                return False, f"Model file not found: {model_path}"

            # Initialize Llama model
            self.llm = Llama(model_path=model_path, n_ctx=2048, verbose=False)
            self.model_path = model_path
            return True, "Model loaded successfully."
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False, f"Failed to load model: {str(e)}"

    def is_loaded(self):
        return self.llm is not None

    def scan_directory_heuristics(self, working_dir):
        """
        Scans working_dir to find a likely input directory containing required subfolders.
        Returns:
            dict: {
                'found_input_dir': path or None,
                'candidates': list of (path, score),
                'missing_keys': list of missing folder names in the best candidate
            }
        """
        if not dataset_config:
            return {'found_input_dir': None, 'candidates': [], 'missing_keys': []}

        # Identify required root folders (e.g. 'P', 'ET', 'LAI') from 'P/Monthly' etc.
        required_folders = [config['subdir'] for config in dataset_config.values()]
        # We look for the top-level folder of the requirements.
        # e.g. if 'P/Monthly', we look for 'P'.
        required_roots = list(set([r.split(os.sep)[0] for r in required_folders]))

        candidates = []

        # Function to score a directory
        def score_directory(path):
            if not os.path.isdir(path):
                return 0, []
            score = 0
            missing = []

            # Get list of actual items in path for case-insensitive matching
            try:
                actual_items = os.listdir(path)
                actual_items_lower = [item.lower() for item in actual_items]
            except OSError:
                return 0, required_roots

            for root in required_roots:
                if root.lower() in actual_items_lower:
                    # Check if it is a directory
                    idx = actual_items_lower.index(root.lower())
                    real_name = actual_items[idx]
                    if os.path.isdir(os.path.join(path, real_name)):
                        score += 1
                        continue
                missing.append(root)
            return score, missing

        # 1. Check working_dir itself
        score, missing = score_directory(working_dir)
        if score > 0:
            candidates.append({'path': working_dir, 'score': score, 'missing': missing})

        # 2. Check subdirectories (depth 1)
        try:
            if os.path.isdir(working_dir):
                subdirs = [os.path.join(working_dir, d) for d in os.listdir(working_dir)
                           if os.path.isdir(os.path.join(working_dir, d))]

                for subdir in subdirs:
                    s, m = score_directory(subdir)
                    if s > 0:
                        candidates.append({'path': subdir, 'score': s, 'missing': m})
        except OSError:
            pass

        # Sort by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)

        best_candidate = None
        if candidates:
            # We consider it a good match if it has at least 3 matching folders
            # (Heuristic: typical dataset has ~8 folders, finding 3 is a strong signal)
            if candidates[0]['score'] >= 3:
                best_candidate = candidates[0]

        return {
            'found_input_dir': best_candidate['path'] if best_candidate else None,
            'candidates': candidates,
            'missing_keys': best_candidate['missing'] if best_candidate else required_roots
        }

    def scan_workspace(self, working_dir):
        """
        Broad scan of the working directory for ALL required files and directories
        defined in file_patterns (from wa_config).

        Returns a dict mapping UI keys to found paths.
        """
        results = {}
        found_count = 0
        missing_keys = []

        # Handle case where a file path is passed instead of a directory
        if working_dir and os.path.isfile(working_dir):
            working_dir = os.path.dirname(working_dir)

        if not working_dir or not os.path.isdir(working_dir):
            return {'found': results, 'count': 0, 'missing': list(file_patterns.keys())}

        # First, run the directory heuristic to find the main input folder (for Tiffs)
        dir_scan = self.scan_directory_heuristics(working_dir)
        if dir_scan['found_input_dir']:
            results['input_tifs'] = dir_scan['found_input_dir']
            found_count += 1
        else:
            missing_keys.append('input_tifs')

        # Now scan for files using patterns
        # We look in the root working_dir and depth 1 subdirectories
        search_dirs = [working_dir]
        try:
             search_dirs.extend([os.path.join(working_dir, d) for d in os.listdir(working_dir)
                                if os.path.isdir(os.path.join(working_dir, d))])
        except OSError:
            pass

        for key, patterns in file_patterns.items():
            found_path = None

            for d in search_dirs:
                if found_path: break
                for pattern in patterns:
                    matches = glob.glob(os.path.join(d, pattern))
                    # Case insensitive fallback if glob is sensitive
                    if not matches:
                         try:
                            all_files = os.listdir(d)
                            for f in all_files:
                                if fnmatch.fnmatch(f.lower(), pattern.lower()):
                                    matches.append(os.path.join(d, f))
                         except OSError:
                             pass

                    if matches:
                        # Heuristic: pick the shortest filename or the one with 'basin' if multiple
                        # For now, just pick the first one
                        found_path = matches[0]
                        break

            if found_path:
                results[key] = found_path
                found_count += 1
            else:
                missing_keys.append(key)

        return {'found': results, 'count': found_count, 'missing': missing_keys}

    def analyze_dataset_quality(self, input_dir):
        """
        Counts files and basic checks.
        """
        if not input_dir or not os.path.exists(input_dir):
            return {"error": "Invalid directory", "details": {}, "total_files": 0}

        report = {}
        total_files = 0

        for key, config in dataset_config.items():
            subdir = config['subdir']
            target_path = os.path.join(input_dir, subdir)

            # Simple check if path exists
            if os.path.exists(target_path):
                files = glob.glob(os.path.join(target_path, '*.tif'))
                # Try .tiff as well
                files += glob.glob(os.path.join(target_path, '*.tiff'))

                count = len(files)
                report[key] = {
                    'count': count,
                    'status': 'OK' if count > 0 else 'Empty',
                    'path': subdir,
                    'display_name': config.get('attrs', {}).get('quantity', key)
                }
                total_files += count
            else:
                report[key] = {
                    'count': 0,
                    'status': 'Missing Directory',
                    'path': subdir,
                    'display_name': config.get('attrs', {}).get('quantity', key)
                }

        return {'details': report, 'total_files': total_files}

    def generate_ai_response(self, context_data, prompt_type="directory_scan"):
        """
        Generates a response using the LLM.
        """
        response_text = ""
        prompt_content = ""

        if prompt_type == "directory_scan":
            # Context data is result of scan_directory_heuristics (legacy) or scan_workspace
            if 'found' in context_data: # scan_workspace result
                found_map = context_data.get('found', {})
                missing = context_data.get('missing', [])
                count = context_data.get('count', 0)

                if count == 0:
                     response_text = "I couldn't find any relevant files in the selected workspace. Please check your folder."
                     prompt_content = "Workspace empty. No files found."
                else:
                    items_found = [k.replace('_', ' ').title() for k in found_map.keys()]
                    items_missing = [k.replace('_', ' ').title() for k in missing]

                    response_text = f"I scanned the workspace and found {count} relevant items:\n"
                    response_text += ", ".join(items_found[:5])
                    if len(items_found) > 5: response_text += ", etc."

                    if missing:
                        response_text += f"\n\nMissing items: {', '.join(items_missing[:5])}"
                        if len(items_missing) > 5: response_text += "..."
                    else:
                        response_text += "\n\nAll required files found!"

                    prompt_content = f"Scan complete. Found: {', '.join(items_found)}. Missing: {', '.join(items_missing)}."

            else: # Legacy heuristic result
                found = context_data.get('found_input_dir')
                missing = context_data.get('missing_keys', [])

                if not found:
                    response_text = "I checked the working directory but couldn't find a valid input dataset folder."
                    prompt_content = f"User selected a directory. No valid input data folders found."
                else:
                    response_text = f"I found a likely input directory at: {os.path.basename(found)}."
                    if missing:
                        response_text += f"\nMissing folders: {', '.join(missing)}."
                    else:
                        response_text += "\nIt looks complete."

                    prompt_content = f"Found input data in '{os.path.basename(found)}'. Missing: {missing}."

        elif prompt_type == "data_analysis":
            # Context data is result of analyze_dataset_quality
            details = context_data.get('details', {})
            total_files = context_data.get('total_files', 0)

            issues = [f"{v['display_name']}: {v['status']}" for k, v in details.items() if v['status'] != 'OK']
            good = [f"{v['display_name']}: {v['count']} files" for k, v in details.items() if v['status'] == 'OK']

            response_text = f"Dataset Analysis:\nTotal Files: {total_files}\n"
            if issues:
                response_text += "Issues found:\n" + "\n".join(issues)
            else:
                response_text += "All required directories exist and contain files."

            prompt_content = f"Dataset report. Total files: {total_files}. Problems: {', '.join(issues)}."

        else:
            return "Unknown context."

        if not self.is_loaded():
            return response_text

        # Run LLM
        try:
            system_prompt = "You are a helpful assistant for a Water Accounting Tool. Be concise, friendly, and professional."
            full_prompt = f"{system_prompt}\nContext: {prompt_content}\nResponse:"
            output = self.llm(full_prompt, max_tokens=150, stop=["Context:", "\nResponse:", "System:"], echo=False)
            generated = output['choices'][0]['text'].strip()
            if generated:
                return generated
            else:
                return response_text
        except Exception as e:
            self.logger.error(f"LLM Error: {e}")
            return response_text + " (AI generation failed)"

    def get_time_series_from_tiffs(self, directory):
        """
        Scan a directory of TIFFs, parse dates, calculate means, and return a DataFrame.
        """
        if not rasterio or not pd:
            return None, "Required libraries (rasterio, pandas) are missing."

        if not os.path.exists(directory):
            return None, f"Directory not found: {directory}"

        files = glob.glob(os.path.join(directory, "*.tif"))
        files += glob.glob(os.path.join(directory, "*.tiff"))

        if not files:
            return None, "No TIFF files found in directory."

        data = []
        dates = []

        # Limit files to prevent freezing
        if len(files) > 100:
            # Sample evenly
            indices = np.linspace(0, len(files)-1, 100, dtype=int)
            files = [files[i] for i in indices]

        # Heuristic for date parsing: look for YYYYMMDD or YYYYMM or YYYY.MM.DD
        # Prioritize patterns
        patterns = [
            r"(\d{4})(\d{2})(\d{2})", # YYYYMMDD
            r"(\d{4})\.(\d{2})\.(\d{2})", # YYYY.MM.DD
            r"(\d{4})-(\d{2})-(\d{2})", # YYYY-MM-DD
            r"(\d{4})(\d{2})" # YYYYMM
        ]

        for f in sorted(files):
            fname = os.path.basename(f)
            dt = None
            for pat in patterns:
                match = re.search(pat, fname)
                if match:
                    parts = [int(g) for g in match.groups()]
                    try:
                        if len(parts) == 3:
                            dt = datetime.datetime(parts[0], parts[1], parts[2])
                        elif len(parts) == 2:
                            dt = datetime.datetime(parts[0], parts[1], 1)
                        break
                    except ValueError:
                        continue

            if dt:
                try:
                    with rasterio.open(f) as src:
                        # Read first band
                        arr = src.read(1, masked=True)
                        # Compute mean, ignoring nodata (masked)
                        mean_val = np.nanmean(arr)
                        # Handle case where everything is masked
                        if np.ma.is_masked(mean_val):
                             if mean_val.mask:
                                 mean_val = np.nan
                             else:
                                 mean_val = float(mean_val)

                        dates.append(dt)
                        data.append(mean_val)
                except Exception as e:
                    self.logger.error(f"Error reading {f}: {e}")

        if not data:
            return None, "Could not extract data from files (check date formats)."

        df = pd.DataFrame({'Date': dates, 'Mean': data})
        df = df.sort_values('Date')
        return df, "Success"

    def plot_data(self, df, title, ylabel):
        """
        Generate a plot from DataFrame and return the path to the image.
        """
        if not plt:
            return None, "Matplotlib is missing."

        try:
            plt.figure(figsize=(10, 5))
            plt.plot(df['Date'], df['Mean'], marker='o', linestyle='-')
            plt.title(title)
            plt.xlabel('Date')
            plt.ylabel(ylabel)
            plt.grid(True)
            plt.tight_layout()

            # Save to temporary file
            fd, path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            plt.savefig(path)
            plt.close()
            return path, "Success"
        except Exception as e:
            self.logger.error(f"Plotting error: {e}")
            return None, str(e)

    def chat(self, user_message, context_info=None):
        """
        Handle conversational chat with the user, incorporating tool context.
        """
        if not self.is_loaded():
            return "I am running in limited mode because the AI model is not loaded. I can still help check data if you ask 'check data' or 'plot precipitation', but conversational abilities are limited."

        if context_info is None:
            context_info = {}

        # 1. Check for Analysis Intents via Regex/Keywords
        msg_lower = user_message.lower()
        intent_analysis = any(x in msg_lower for x in ['plot', 'graph', 'trend', 'show me'])

        if intent_analysis:
            # Try to identify variable
            # Map common names to config keys
            var_map = {
                'precipitation': 'P', 'rain': 'P', 'rainfall': 'P',
                'evapotranspiration': 'ET', 'et': 'ET', 'eta': 'ET',
                'lai': 'LAI', 'leaf area': 'LAI',
                'soil moisture': 'SMsat', 'theta': 'SMsat',
                'ndm': 'ProbaV', 'biomass': 'ProbaV',
                'aridity': 'Ari'
            }

            target_var = None
            for key, val in var_map.items():
                if key in msg_lower:
                    target_var = val
                    break

            # If no mapping found, check direct config keys (case insensitive)
            if not target_var:
                for key in dataset_config.keys():
                    if key.lower() in msg_lower:
                        target_var = key
                        break

            if target_var:
                # Find the path
                found_files = context_info.get('found_files', {})
                # 'input_tifs' usually points to the root input dir.
                # We need to append the subdirectory from config.

                base_dir = found_files.get('input_tifs')
                if base_dir:
                    subdir = dataset_config.get(target_var, {}).get('subdir')
                    if subdir:
                        full_path = os.path.join(base_dir, subdir)

                        # Generate Plot
                        df, msg = self.get_time_series_from_tiffs(full_path)
                        if df is not None and not df.empty:
                            unit = dataset_config.get(target_var, {}).get('attrs', {}).get('units', 'Value')
                            display_name = f"{target_var} Trend"
                            img_path, plt_msg = self.plot_data(df, display_name, unit)

                            if img_path:
                                return f"Here is the trend for {target_var} based on the input files in '{subdir}'.\n[IMAGE: {img_path}]"
                            else:
                                return f"I could read the data but failed to generate the plot: {plt_msg}"
                        else:
                            return f"I tried to analyze {target_var} in '{full_path}' but couldn't extract time series data. {msg}"
                    else:
                        return f"Configuration for {target_var} is missing subdirectory info."
                else:
                    return "I know you want to plot data, but I haven't found the input directory yet. Please select the Working Directory first."

        # 2. General LLM Chat
        # Construct System Prompt with Data Analyst Persona
        system_prompt = """You are Jules, a Data Analysis Assistant for the Water Accounting Plus (WA+) Tool.
Your goal is to help users inspect their input data and understand the files.

Capabilities:
- You can plot trends if the user asks (e.g., "plot precipitation").
- You can explain what files are needed (P, ET, LAI, etc.).

Code Structure:
- Input data is stored in TIFF files in specific subfolders.
- 'main_app.py' controls the application.

Instructions:
- If asked about specific data, encourage the user to ask for a plot or check.
- Do NOT suggest running workflows like 'hydroloop' or 'netcdf creation' anymore; focus on data inspection.
- Be concise, professional, and helpful.
"""

        # Context summary
        ctx_str = ""
        if 'working_dir' in context_info:
            ctx_str += f"Current Working Directory: {context_info['working_dir']}\n"

        found = context_info.get('found_files', {})
        if found:
            ctx_str += f"Found Files: {', '.join(found.keys())}\n"

        full_prompt = f"System: {system_prompt}\nContext: {ctx_str}\nUser: {user_message}\nAssistant:"

        try:
            output = self.llm(full_prompt, max_tokens=200, stop=["User:", "System:"], echo=False)
            response = output['choices'][0]['text'].strip()
            return response
        except Exception as e:
            self.logger.error(f"Chat LLM Error: {e}")
            return "I encountered an error generating a response. Please try again."
