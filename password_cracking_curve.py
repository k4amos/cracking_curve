#!/usr/bin/env python3
"""
Password Cracking Progress Visualization Tool
Visualize hashcat password cracking progress in real-time with interactive curves.
"""

import json
import sys
from pathlib import Path
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go
import argparse


class HashcatStatusParser:
    """Parse and process Hashcat JSON status outputs."""

    def __init__(self, filename, x_axis_type='guesses', y_axis_type='percentage', status_timer=1):
        self.filename = filename
        self.x_axis_type = x_axis_type
        self.y_axis_type = y_axis_type
        self.status_timer = status_timer

    def parse_status_file(self):
        """
        Parse Hashcat JSON lines and group points by (guess_base, guess_mod).
        Returns curves data for plotting.
        """
        curves_x = []
        curves_y = []
        label_list = []

        path = Path(self.filename)
        if not path.exists():
            return curves_x, curves_y, label_list

        guesses = 0
        current_identifier = ""
        elapsed_seconds = 0

        with open(self.filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("{"):
                    continue

                try:
                    data = json.loads(line)

                    # Extract core values
                    progress = data.get("progress", [0])[0]
                    guesses += progress

                    recovered = data.get("recovered_hashes", [0, 0])
                    cracked = recovered[0]
                    total = recovered[1] if recovered[1] > 0 else 1

                    # X-axis value
                    if self.x_axis_type == 'time':
                        x_value = elapsed_seconds
                    else:  # 'guesses'
                        x_value = guesses

                    # Y-axis value
                    if self.y_axis_type == 'count':
                        y_value = cracked
                    else:  # 'percentage'
                        y_value = (cracked / total) * 100

                    # Extract attack info
                    guess_base = data.get("guess", {}).get("guess_base", "unknown")
                    guess_base = guess_base.replace("autocat_new_cracked_potfile", "potfile")
                    guess_mod = data.get("guess", {}).get("guess_mod", None)
                    time_start = data.get("time_start", "unknown")

                    key = (f"{time_start}/{guess_base}", guess_mod)

                    # Handle new attack phase
                    if key != current_identifier:
                        if current_identifier != "":
                            # Close previous curve
                            curves_x.append([curves_x[-1][-1], x_value])
                            curves_y.append([curves_y[-1][-1], y_value])
                        else:
                            # First curve
                            curves_x.append([0, x_value])
                            curves_y.append([0, y_value])
                        current_identifier = key
                        label_list.append(key)
                    else:
                        # Continue current curve
                        curves_x[-1].append(x_value)
                        curves_y[-1].append(y_value)

                    # Increment time counter for next iteration
                    elapsed_seconds += self.status_timer

                except json.JSONDecodeError:
                    continue

        return curves_x, curves_y, label_list


class PasswordCrackingApp:
    """Main application for visualizing password cracking progress."""

    def __init__(self, hashcat_files):
        self.hashcat_files = hashcat_files if isinstance(hashcat_files, list) else [hashcat_files]

        # Default values
        self.update_interval = 10000  # 10 seconds in milliseconds
        self.x_axis_type = 'guesses'
        self.y_axis_type = 'percentage'
        self.status_timer = 1
        self.no_potfile_highlight = False

        # Initialize parsers
        self.update_parsers()

        # Initialize Dash app
        self.app = Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()

    def update_parsers(self):
        """Update parsers with current settings."""
        self.parsers = {file: HashcatStatusParser(file, self.x_axis_type, self.y_axis_type, self.status_timer)
                        for file in self.hashcat_files}

    def _setup_layout(self):
        """Setup the Dash app layout with controls."""
        file_list = ", ".join([Path(f).name for f in self.hashcat_files])

        self.app.layout = html.Div([
            html.H2("Password Cracking Progress Visualization", style={'text-align': 'center'}),

            # Control panel
            html.Div([
                html.Div([
                    html.Label("Refresh Interval (seconds):"),
                    dcc.Input(
                        id='refresh-input',
                        type='number',
                        value=10,
                        min=1,
                        max=300,
                        style={'width': '100px', 'margin-left': '10px'}
                    )
                ], style={'margin': '10px', 'display': 'inline-block'}),


                html.Div([
                    html.Label("X-Axis:"),
                    dcc.RadioItems(
                        id='x-axis-radio',
                        options=[
                            {'label': 'Number of hashes', 'value': 'guesses'},
                            {'label': 'Time (seconds)', 'value': 'time'}
                        ],
                        value='guesses',
                        inline=True,
                        style={'margin-left': '10px'}
                    )
                ], style={'margin': '10px', 'display': 'inline-block'}),

                html.Div([
                    html.Label("Y-Axis:"),
                    dcc.RadioItems(
                        id='y-axis-radio',
                        options=[
                            {'label': 'Percentage', 'value': 'percentage'},
                            {'label': 'Count', 'value': 'count'}
                        ],
                        value='percentage',
                        inline=True,
                        style={'margin-left': '10px'}
                    )
                ], style={'margin': '10px', 'display': 'inline-block'}),

                html.Div([
                    dcc.Checklist(
                        id='potfile-highlight-check',
                        options=[
                            {'label': 'Highlight potfile attacks in black', 'value': 'highlight'}
                        ],
                        value=['highlight'],
                        style={'margin-left': '10px'}
                    )
                ], style={'margin': '10px', 'display': 'inline-block'}),

                html.Button('Update', id='update-button', n_clicks=0,
                           style={'margin': '10px', 'padding': '5px 20px'})

            ], style={'background-color': '#f0f0f0', 'padding': '10px', 'border-radius': '5px'}),

            html.Div([
                html.P(f"Data sources: {file_list}", style={'font-style': 'italic'})
            ], style={'margin': '10px'}),

            dcc.Graph(id="live-graph", style={'height': '80vh'}),
            dcc.Interval(id="interval-component", interval=self.update_interval, n_intervals=0)
        ])

    def _setup_callbacks(self):
        """Setup Dash callbacks for live updates and controls."""

        @self.app.callback(
            [Output("interval-component", "interval"),
             Output("live-graph", "figure")],
            [Input("interval-component", "n_intervals"),
             Input("update-button", "n_clicks")],
            [State("refresh-input", "value"),
             State("x-axis-radio", "value"),
             State("y-axis-radio", "value"),
             State("potfile-highlight-check", "value")]
        )
        def update_graph_and_settings(n_intervals, n_clicks, refresh, x_axis, y_axis, potfile_highlight):
            ctx = callback_context

            # Update settings if button was clicked
            if ctx.triggered and ctx.triggered[0]['prop_id'] == 'update-button.n_clicks':
                self.update_interval = refresh * 1000
                self.x_axis_type = x_axis
                self.y_axis_type = y_axis
                self.no_potfile_highlight = 'highlight' not in potfile_highlight
                self.update_parsers()

            # Create figure
            figure = self._create_figure()

            return self.update_interval, figure

    def _create_figure(self):
        """Create the plotly figure with current data from all files."""
        fig = go.Figure()

        # Configure axis labels
        x_axis_title = "Time (seconds)" if self.x_axis_type == 'time' else "Number of hashes tested"
        y_axis_title = "Cracked passwords (count)" if self.y_axis_type == 'count' else "Cracked passwords (%)"

        # Color palette for different files
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']

        # Process each file
        for file_idx, (file_path, parser) in enumerate(self.parsers.items()):
            curves_x, curves_y, label_list = parser.parse_status_file()
            file_name = Path(file_path).stem
            file_color = colors[file_idx % len(colors)]

            for k in range(len(curves_x)):
                # Downsample large datasets
                if len(curves_x[k]) > 1000:
                    sample_rate = 60
                    curves_x_sampled = curves_x[k][::sample_rate]
                    curves_y_sampled = curves_y[k][::sample_rate]

                    # Ensure last point is included
                    if (len(curves_x[k]) - 1) % sample_rate != 0:
                        curves_x_sampled.append(curves_x[k][-1])
                        curves_y_sampled.append(curves_y[k][-1])

                    curves_x[k] = curves_x_sampled
                    curves_y[k] = curves_y_sampled

                # Extract label info
                (guess_base, guess_mod) = label_list[k]
                attack_label = f"{guess_base.split('/')[-1]} {guess_mod.split('/')[-1]}" if guess_mod != None else guess_base.split('/')[-1]

                # Special handling for potfile - use black unless disabled
                if "potfile" in guess_base and not self.no_potfile_highlight:
                    color = "black"
                else:
                    color = None

                fig.add_trace(go.Scatter(
                    x=curves_x[k],
                    y=curves_y[k],
                    mode="lines",
                    marker_color=color,
                    name=attack_label,
                    legendgroup=file_name,
                    legendgrouptitle_text=file_name if k == 0 else None
                ))

        fig.update_layout(
            xaxis_title=x_axis_title,
            yaxis_title=y_axis_title,
            template="plotly_white",
            legend=dict(title="Files and Attack Phases"),
            hovermode='x unified',
            margin=dict(t=30, b=60)
        )

        return fig

    def run(self, debug=False, host='127.0.0.1', port=8050):
        """Run the Dash application."""
        self.app.run(debug=debug, host=host, port=port)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Password Cracking Progress Visualization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s output.json
      Display cracking progress from a single file

  %(prog)s output1.json output2.json output3.json
      Compare multiple cracking sessions simultaneously

  %(prog)s *.json
      Load all JSON files in the current directory

All visualization settings can be controlled through the web interface.

Note: The input files should contain hashcat JSON status outputs
      generated with: hashcat --status-json --status-timer 1 --status ...
"""
    )

    parser.add_argument('files', nargs='+',
                        help='Path(s) to hashcat JSON output file(s)')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Host to run the server on (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8050,
                        help='Port to run the server on (default: 8050)')

    args = parser.parse_args()

    # Validate files exist
    for file_path in args.files:
        if not Path(file_path).exists():
            print(f"Error: File '{file_path}' not found!", file=sys.stderr)
            sys.exit(1)

    # Create and run app
    app = PasswordCrackingApp(hashcat_files=args.files)

    print("Starting Password Cracking Visualization...")
    print(f"Dashboard available at: http://{args.host}:{args.port}")
    print("All settings can be controlled through the web interface.")
    print("Press Ctrl+C to stop")

    app.run(debug=args.debug, host=args.host, port=args.port)


if __name__ == "__main__":
    main()