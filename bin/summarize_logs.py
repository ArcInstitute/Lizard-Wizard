#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import re
import os
import sys
import argparse
import concurrent.futures
## 3rd party
import markdown
import openai

# argparse
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass

desc = "Summarize pipeline log files"
epi = """DESCRIPTION:
Summarize log files from the pipeline using an LLM.
Warnings and errors are prioritized
"""
parser = argparse.ArgumentParser(description=desc, epilog=epi,
                                 formatter_class=CustomFormatter)
parser.add_argument("log_file", type=str, nargs="+",
                    help="log file to summarize.")
parser.add_argument("-o", "--output-dir", type=str, default="output",
                    help="Output directory.")
parser.add_argument("-O", "--output-prefix", type=str, default="final_summary",
                    help="Output directory.")
parser.add_argument("-m", "--model", type=str, default="gpt-4o-mini",
                    choices=["gpt-4o-mini", "gpt-4o"],
                    help="openai model to use.")
parser.add_argument("-M", "--max-lines", type=int, default=5000,
                    help="Max lines to summarize.")
parser.add_argument("-f", "--final-summary", action="store_true", default=False,
                    help="Summarize all summaries.")
parser.add_argument("-t", "--threads", type=int, default=1,
                    help="Number of threads to use.")

# functions
def summarize_log(log_content: str, client: openai.Client, model: str="gpt-4o-mini", 
                  max_tokens: int=1000, final_summary: bool=False) -> str:
    """
    Use the openai client to summarize the log content.
    Args:
        log_content: the log content to summarize
        client: openai client
        max_tokens: max tokens for the completion
    Returns:
        str: the LLM-generated summary
    """
    # system prompt
    if final_summary:
        system_prompt = "Create a final summary report for the following markdown summary reports."
        "Each summary report provided to you is a summary of log files for various steps of a bioinformatics pipeline."
        "Be sure to clearly describe any errors or warnings noted in any of the summary reports."
        "Format the final report in markdown with headers for each step in the pipeline."
    else:
        system_prompt = "Summarize the following log file content."
        "Each log file is from a step in a bioinformatics pipeline."
        "Note the name of the pipeline step in the summary."
        "Format the summary in markdown."
    system_prompt += "Prioritize errors and warnings. Generally, do not note the time of any log entry in your report."
    # generate completion
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": log_content}
        ],
        max_tokens=max_tokens
    )
    # return the completion content
    return completion.choices[0].message.content

def write_blank_files(log_files: list, output_dir: str):
    """
    Write out blank output files for each log file.
    Args:
        log_files: list of log files
        output_dir: output directory
    """
    for log_file in log_files:
        outfile_base = os.path.splitext(os.path.basename(log_file))[0] + "_summary.md"
        outfile = os.path.join(output_dir,  outfile_base)
        open(outfile, "w").close()
        print(f"  Blank summary written to {outfile}", file=sys.stderr)

def read_log(infile: str, max_lines: int) -> str:
    """
    Read the log file.
    Args:
        infile: input log file
    Returns:
        str: the log content
    """
    regex = re.compile(r"^/.+/([0-9A-Za-z_.]+\.py):[0-9]+:")
    content = []
    last_line = ""
    last_prefix = ""
    last_py = ""
    with open(infile) as inF:
        for line in inF:
            line = line.rstrip()
            # filter redundant lines
            ## redundant full lines
            if line == last_line:
                continue
            ## redundant prefix
            prefix = line.split(" ", 1)[0]
            if prefix == last_prefix:
                continue
            ## redundant python file
            match = regex.match(prefix)
            if match:
                py = match.group(1)
                if py == last_py:
                    continue
                last_py = py
            content.append(line)
            # update last line
            last_line = line
            last_prefix = prefix
    # truncate if necessary
    if len(content) >= max_lines:
        print(f"Truncating log file to {max_lines} lines", file=sys.stderr)
        content = content[:max_lines]
        content.append(f'... (truncated to {max_lines} lines)')
    return "\n".join(content)

def md2html(markdown_text: str, outfile: str):
    """
    Convert markdown to html.
    Args:
        markdown_text: markdown content
        outfile: output file
    """
    # convert markdown to html
    html = markdown.markdown(markdown_text, tab_length=2)

    # Define custom CSS (you can load this from a file too)
    css = """
<style>
    body { font-family: Arial, sans-serif; line-height: 1.4; }
    h1, h2, h3 { padding-bottom: 2px; margin-top: 10px; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    table, th, td { border: 1px solid #ddd; padding: 8px; }
    th { background-color: #f2f2f2; }
    ol { margin-left: 6px; }
    ul { margin-left: 6px; }
</style>
"""
    # Write out the HTML and CSS together
    with open(outfile, "w") as outF:
        outF.write(f"{css}\n{html}")

    # Status
    print(f"  HTML written to {outfile}", file=sys.stderr)

def process_log_file(log_file: str, output_dir: str, client: openai.Client,
                     model: str="gpt-4o-mini", max_lines: int=5000, 
                     final_summary: bool=False) -> str:
    print(f"Processing {log_file}", file=sys.stderr)

    # Read the log file
    log_content = read_log(log_file, max_lines)
        
    # Summarize the log file
    summary = summarize_log(log_content, client, model=model, final_summary=final_summary)
        
    # Write the summary to a file
    outfile_base = os.path.splitext(os.path.basename(log_file))[0] + "_summary.md"
    outfile = os.path.join(output_dir,  outfile_base)
    with open(outfile, "w") as f:
        log_file_basename = os.path.basename(log_file)
        f.write(f"#-- Log file: {log_file_basename}  --#\n\n")
        f.write(summary + "\n\n")
    print(f"  Summary written to {outfile}", file=sys.stderr)

    # Return summary text
    return f"--- {outfile_base} ---\n" + summary + "\n\n"

def main(args):
    # Output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Check for OPENAI_API_KEY
    if os.getenv("OPENAI_API_KEY") is None:
        print("WARNING: No OPENAI_API_KEY environment variable", file=sys.stderr)
        # write out blank output files
        write_blank_files(args.log_files, args.output_dir)
        exit()

    # Create openai client
    client = openai.Client()
    
    # Process each log file in parallel
    all_summaries = ""
    regex = re.compile(r"_summary.md$")
    if args.final_summary:
        for log_file in args.log_file:
            with open(log_file) as inF:
                step_name = regex.sub("", os.path.basename(log_file))
                all_summaries += f"#-- Pipeline step: {step_name}  --#\n\n"
                all_summaries += inF.read()
                all_summaries += "\n\n"
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            # Process each log file
            futures = []
            for log_file in args.log_file:
                futures.append(
                   executor.submit(
                        process_log_file, 
                        log_file, args.output_dir, client, 
                        model=args.model, 
                        max_lines=args.max_lines,
                        final_summary=args.final_summary
                    )
                )
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                all_summaries += future.result()

    # summarize all summaries
    print("Summarizing all log file summaries", file=sys.stderr)
    summary = summarize_log(all_summaries, openai, max_tokens=1500)
    outfile = os.path.join(args.output_dir, f"{args.output_prefix}.md")
    with open(outfile, "w") as outF:
        outF.write(summary + "\n")
    print(f"  Summary written to {outfile}", file=sys.stderr)

    # Convert to html
    print("Converting final summary to HTML", file=sys.stderr)
    outfile = os.path.join(args.output_dir, f"{args.output_prefix}.html")
    md2html(summary, outfile)
    
## script main
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
