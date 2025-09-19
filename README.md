# Password Cracking Progress Visualization

A real-time visualization tool for monitoring Hashcat / Autocat password cracking progress with interactive curves.

Autocat cracking curve of this 2014 [public leak](https://github.com/YoureIronic/Historical-Data-Breaches-Archive/blob/main/breaches/Dominos/index.md) : 
<p align="center">
    <img src="img/exemple.png" style="height:350px">
</p>

⚠️ The README is currently under construction.

## Features

- **Real-time Updates**: Monitor cracking progress as it happens
- **Interactive Controls**: All settings adjustable through the web interface
- **Multiple Visualization Options**:
  - X-axis: Number of hashes tested or elapsed time
  - Y-axis: Percentage cracked or absolute count
- **Multi-file Support**: Compare multiple cracking sessions simultaneously
- **Interactive Dashboard**: Web-based interface using Plotly and Dash
- **Attack Phase Tracking**: Visualize different attack phases (wordlists, rules, etc.)
- **Automatic Data Sampling**: Handles large datasets efficiently

## Requirements

- Python 3.6+
- Dash
- Plotly
- Hashcat (for generating input data)

## Installation

```bash
pip install dash plotly
```

## Usage

### Basic Usage

```bash
# Single file
python password_cracking_curve.py output.json

# Multiple files
python password_cracking_curve.py output1.json output2.json output3.json

# All JSON files in directory
python password_cracking_curve.py *.json
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `files` | Path(s) to hashcat JSON output file(s) (required) | - |
| `--host` | Server host address | 127.0.0.1 |
| `--port` | Server port | 8050 |
| `--debug` | Enable debug mode | False |
| `-h, --help` | Show help message | - |

### Interactive Controls

Once the dashboard is running, you can control all visualization settings through the web interface:

- **Refresh Interval**: How often the graph updates (1-300 seconds)
- **X-Axis**: Toggle between number of hashes tested or time elapsed
- **Y-Axis**: Toggle between percentage or count of cracked passwords
- **Potfile Highlighting**: Option to highlight potfile attacks in black

Click the "Update" button to apply any changes.

## Generating Input Data

The tool requires Hashcat JSON status output. Generate it using:

```bash
hashcat [options] --status-json --status-timer 1 --status > output.json
```

Example:

```bash
hashcat -m 0 -a 0 hashes.txt wordlist.txt -r rules.rule \
    --status-json --status-timer 1 --status > cracking_progress.json
```

It also works with Autocat : https://github.com/k4amos/Autocat

## Input File Format

The tool expects a file containing JSON status lines from Hashcat:

```json
{"status": 1, "progress": [1000], "recovered_hashes": [5, 100], "time_start": 1234567890, ...}
{"status": 1, "progress": [2000], "recovered_hashes": [10, 100], "time_start": 1234567890, ...}
```

## Visualization Features

- **Multiple Files Support**: Compare different cracking sessions on the same graph
- **File Distinction**: Each file gets a unique color palette with file name prefix in labels
- **Curve Colors**: Potfile attacks can be highlighted in black (optional)
- **Legend Grouping**: Curves are grouped by source file in the legend
- **Hover Information**: Unified hover mode shows all curves' values at cursor position
- **Auto-sampling**: Large datasets (>1000 points) are automatically downsampled for performance

## Example Workflow

1. Start your Hashcat attack with JSON status output:
   ```bash
   hashcat -m 0 -a 0 hashes.txt wordlist.txt --status-json --status-timer 1 > progress.json
   ```

2. In another terminal, start the visualization:
   ```bash
   python password_cracking_curve.py progress.json
   ```

3. Open your browser to `http://localhost:8050`

4. Adjust visualization settings through the web interface

5. Watch the cracking progress in real-time!

## Troubleshooting

- **ImportError**: Install required packages with `pip install dash plotly`
- **File not found**: Ensure the input file path is correct and the file exists
- **No data displayed**: Verify the input file contains valid Hashcat JSON status lines
- **Connection refused**: Check if the port is already in use or firewall settings

## License

This tool is provided as-is for security analysis and defensive purposes only.
