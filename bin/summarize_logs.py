#!/usr/bin/env python
# import
## batteries
from __future__ import print_function
import re
import os
import sys
import argparse
## 3rd party
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
parser.add_argument("-m", "--model", type=str, default="gpt-4o-mini",
                    choices=["gpt-4o-mini", "gpt-4o"],
                    help="openai model to use.")
parser.add_argument("-M", "--max-lines", type=int, default=5000,
                    help="Max lines to summarize.")


# functions
def summarize_log(log_content: str, client: openai.Client, model: str="gpt-4o-mini", max_tokens: int=1000) -> str:
    """
    Use the openai client to summarize the log content.
    Args:
        log_content: the log content to summarize
        client: openai client
        max_tokens: max tokens for the completion
    Returns:
        str: the LLM-generated summary
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Summarize the following log file content, prioritizing warnings and errors."},
            {"role": "user", "content": log_content}
        ],
        max_tokens=max_tokens
    )
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

# functions
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
    
    # Process each log file
    all_summaries = ""
    for log_file in args.log_file:
        print(f"Processing {log_file}", file=sys.stderr)

        # Read the log file
        log_content = read_log(log_file, args.max_lines)
        
        # Summarize the log file
        summary = summarize_log(log_content, client, model=args.model)
        
        # Write the summary to a file
        outfile_base = os.path.splitext(os.path.basename(log_file))[0] + "_summary.md"
        outfile = os.path.join(args.output_dir,  outfile_base)
        with open(outfile, "w") as f:
            log_file_basename = os.path.basename(log_file)
            f.write(f"#-- Log file: {log_file_basename}  --#\n\n")
            f.write(summary + "\n\n")
        print(f"  Summary written to {outfile}", file=sys.stderr)

        # Append to summaries
        all_summaries += f"--- {outfile_base} ---\n" + summary + "\n\n"

    # summarize all summaries
    print("Summarizing all log file summaries", file=sys.stderr)
    summary = summarize_log(all_summaries, openai, max_tokens=1500)
    outfile = os.path.join(args.output_dir, "final_summary.md")
    with open(outfile, "w") as f:
        f.write(summary + "\n")
    print(f"  Summary written to {outfile}", file=sys.stderr)

    
## script main
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
