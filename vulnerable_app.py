# vulnerable_app.py
# This is the vulnerable web server for the Blue Team.
# It contains a command injection flaw.

from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)

# A simple HTML template for the ping form.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Ping Utility</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; margin: 40px; }
        .container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2, h3 { color: #333; }
        input[type="text"] { width: 70%; padding: 8px; border-radius: 4px; border: 1px solid #ddd; }
        input[type="submit"] { padding: 8px 15px; border-radius: 4px; border: none; background-color: #007bff; color: white; cursor: pointer; }
        pre { background-color: #eee; padding: 10px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Enter an IP to Ping</h2>
        <form method="post" action="/">
            <input type="text" name="ip_address" size="30" placeholder="e.g., 8.8.8.8">
            <input type="submit" value="Ping">
        </form>
        <hr>
        <h3>Result:</h3>
        <pre>{{ result }}</pre>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result_text = ""
    if request.method == 'POST':
        ip = request.form.get('ip_address')
        if ip:
            # THE VULNERABILITY IS HERE!
            # The 'ip' variable is passed directly to the shell without any checks.
            # An attacker can add a semicolon and another command, like "8.8.8.8; ls -la"
            command = f"ping -c 1 {ip}"
            print(f"Executing vulnerable command: {command}")

            try:
                # Using shell=True with untrusted user input is extremely dangerous!
                result_text = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                result_text = f"Error executing command:\n{e.output}"
    
    return render_template_string(HTML_TEMPLATE, result=result_text)

if __name__ == '__main__':
    print("--- Starting Vulnerable Ping Server on http://0.0.0.0:5000 ---")
    # Make sure to run on 0.0.0.0 to be accessible across the network (and from other Docker containers).
    app.run(host='0.0.0.0', port=5000)

