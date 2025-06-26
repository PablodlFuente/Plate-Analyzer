"""
Module for generating HTML content for plate data visualization.
"""

def generate_html_content(figures_2d, figures_2d_norm, figures_3d, figures_3d_norm):
    """
    Generate HTML content to visualize 2D and 3D figures, both original and normalized.
    """
    # Start with the initial HTML content
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Plate Analysis Results</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        .container { 
            width: 100%; 
            margin: 0 auto; 
        }
        select { 
            padding: 8px; 
            margin-bottom: 20px; 
            width: 300px; 
        }
        .plot-container { 
            width: 100%; 
            min-height: 600px; 
            margin-bottom: 20px;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
            font-weight: bold;
        }
        .tabcontent {
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
        .tabcontent.active {
            display: block;
        }
        .controls {
            margin: 10px 0;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .export-btn { 
            padding: 8px 16px; 
            background-color: #4CAF50; 
            color: white; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            margin-left: 10px;
        }
        .export-btn:hover { 
            background-color: #45a049; 
        }
        .checkbox-container {
            display: inline-block;
            margin-right: 15px;
        }
        .checkbox-label {
            margin-left: 5px;
            cursor: pointer;
        }
        .slider-container {
            margin: 20px 0;
            width: 100%;
        }
        .slider {
            -webkit-appearance: none;
            width: 100%;
            height: 15px;
            border-radius: 5px;
            background: #d3d3d3;
            outline: none;
            opacity: 0.7;
            -webkit-transition: .2s;
            transition: opacity .2s;
        }
        .slider:hover {
            opacity: 1;
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }
        .slider::-moz-range-thumb {
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
        }
        .split-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .split-plot {
            width: 100%;
            height: 600px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Plate Analysis Results</h1>
        <div class="controls">
            <select id="plot-selector" onchange="showPlot(this.value)">
"""
    
    # Add plot options
    for i, key in enumerate(figures_2d.keys()):
        selected = "selected" if i == 0 else ""
        html_content += f'                <option value="{key}" {selected}>{key}</option>\n'
    
    # Continue with the rest of the HTML
    html_content += """
            </select>
            <button class="export-btn" onclick="exportCurrentPlot()">Export as PNG</button>
            <div class="checkbox-container">
                <input type="checkbox" id="log-scale-checkbox" onchange="toggleLogScale()">
                <label for="log-scale-checkbox" class="checkbox-label">Log Scale (Y-axis)</label>
            </div>
        </div>
        
        <!-- Tab links -->
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, '2D')">2D View</button>
            <button class="tablinks" onclick="openTab(event, '3D')">3D View</button>
        </div>
        
        <!-- Tab content -->
        <div id="2D" class="tabcontent active">
            <div class="split-container">
                <div id="plot-container-2d" class="split-plot"></div>
                <div id="plot-container-2d-norm" class="split-plot"></div>
            </div>
        </div>
        
        <div id="3D" class="tabcontent">
            <div class="split-container">
                <div id="plot-container-3d" class="split-plot"></div>
                <div id="plot-container-3d-norm" class="split-plot"></div>
            </div>
        </div>
    </div>

    <script>
        // Store all the figures
        const figures2D = {};
        const figures2DNorm = {};
        const figures3D = {};
        const figures3DNorm = {};
        
        // Track log scale state
        let useLogScale = false;
        
        // Function to handle window resize
        function handleResize() {
            // No need to adjust sizes dynamically, we're using fixed dimensions
            const currentKey = document.getElementById('plot-selector').value;
            showPlot(currentKey);
        }
        
        // Add resize event listener
        window.addEventListener('resize', handleResize);
"""

    # Add each original 2D figure as JSON
    for key, fig in figures_2d.items():
        fig_json = fig.to_json()
        html_content += f'        figures2D["{key}"] = {fig_json};\n'

    # Add each normalized 2D figure as JSON
    for key, fig in figures_2d_norm.items():
        fig_json = fig.to_json()
        html_content += f'        figures2DNorm["{key}"] = {fig_json};\n'

    # Add each original 3D figure as JSON
    for key, fig3d in figures_3d.items():
        fig3d_json = fig3d.to_json()
        html_content += f'        figures3D["{key}"] = {fig3d_json};\n'

    # Add each normalized 3D figure as JSON
    for key, fig3d_norm in figures_3d_norm.items():
        fig3d_json = fig3d_norm.to_json()
        html_content += f'        figures3DNorm["{key}"] = {fig3d_json};\n'

    # Add the JavaScript functions
    html_content += """
        // Function to show the selected plot
        function showPlot(key) {
            // Get active tab
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            if (tabName === '2D View') {
                // Show 2D plot (original)
                const currentFigure = JSON.parse(JSON.stringify(figures2D[key]));
                
                // Apply log scale if checkbox is checked
                if (useLogScale) {
                    currentFigure.layout.yaxis = currentFigure.layout.yaxis || {};
                    currentFigure.layout.yaxis.type = 'log';
                } else {
                    currentFigure.layout.yaxis = currentFigure.layout.yaxis || {};
                    currentFigure.layout.yaxis.type = 'linear';
                }
                
                // Make sure the layout is responsive but with fixed dimensions
                currentFigure.layout.autosize = false;
                currentFigure.layout.width = 600;
                currentFigure.layout.height = 500;
                
                Plotly.react('plot-container-2d', currentFigure.data, currentFigure.layout);
                
                // Show 2D plot (normalized)
                const currentFigureNorm = JSON.parse(JSON.stringify(figures2DNorm[key]));
                
                // Apply log scale if checkbox is checked
                if (useLogScale) {
                    currentFigureNorm.layout.yaxis = currentFigureNorm.layout.yaxis || {};
                    currentFigureNorm.layout.yaxis.type = 'log';
                } else {
                    currentFigureNorm.layout.yaxis = currentFigureNorm.layout.yaxis || {};
                    currentFigureNorm.layout.yaxis.type = 'linear';
                }
                
                // Make sure the layout is responsive but with fixed dimensions
                currentFigureNorm.layout.autosize = false;
                currentFigureNorm.layout.width = 600;
                currentFigureNorm.layout.height = 500;
                
                Plotly.react('plot-container-2d-norm', currentFigureNorm.data, currentFigureNorm.layout);
            } else {
                // Show 3D plot (original)
                const currentFigure = JSON.parse(JSON.stringify(figures3D[key]));
                
                // Make sure the layout is responsive but with fixed dimensions
                currentFigure.layout.autosize = false;
                currentFigure.layout.width = 600;
                currentFigure.layout.height = 500;
                
                Plotly.react('plot-container-3d', currentFigure.data, currentFigure.layout);
                
                // Show 3D plot (normalized)
                const currentFigureNorm = JSON.parse(JSON.stringify(figures3DNorm[key]));
                
                // Make sure the layout is responsive but with fixed dimensions
                currentFigureNorm.layout.autosize = false;
                currentFigureNorm.layout.width = 600;
                currentFigureNorm.layout.height = 500;
                
                Plotly.react('plot-container-3d-norm', currentFigureNorm.data, currentFigureNorm.layout);
            }
        }
        
        // Function to toggle log scale
        function toggleLogScale() {
            useLogScale = document.getElementById('log-scale-checkbox').checked;
            showPlot(document.getElementById('plot-selector').value);
        }
        
        // Function to export the current plot as PNG
        function exportCurrentPlot() {
            const currentKey = document.getElementById('plot-selector').value;
            const activeTab = document.querySelector('.tablinks.active');
            const tabName = activeTab.textContent.trim();
            
            // Create a new window to show combined image
            const w = window.open();
            w.document.write('<html><head><title>Export Plots</title></head><body>');
            w.document.write('<h2>Exporting plots...</h2>');
            w.document.write('<p>Right-click on the images to save them.</p>');
            
            if (tabName === '2D View') {
                // Export both 2D plots
                Plotly.toImage('plot-container-2d', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Original 2D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Original 2D Plot"/>');
                });
                
                Plotly.toImage('plot-container-2d-norm', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Normalized 2D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Normalized 2D Plot"/>');
                    w.document.write('</body></html>');
                });
            } else {
                // Export both 3D plots
                Plotly.toImage('plot-container-3d', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Original 3D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Original 3D Plot"/>');
                });
                
                Plotly.toImage('plot-container-3d-norm', {
                    format: 'png',
                    width: 1200,
                    height: 800
                }).then(function(dataUrl) {
                    w.document.write('<h3>Normalized 3D Plot</h3>');
                    w.document.write('<img src="' + dataUrl + '" alt="Normalized 3D Plot"/>');
                    w.document.write('</body></html>');
                });
            }
        }
        
        // Function to open tab
        function openTab(evt, tabName) {
            // Declare all variables
            var i, tabcontent, tablinks;
            
            // Get all elements with class="tabcontent" and hide them
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }
            
            // Get all elements with class="tablinks" and remove the class "active"
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            
            // Show the current tab, and add an "active" class to the button that opened the tab
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
            
            // Update the plot
            showPlot(document.getElementById('plot-selector').value);
        }
        
        // Show the first plot by default
        showPlot(document.getElementById('plot-selector').value);
    </script>
</body>
</html>
"""

    return html_content
