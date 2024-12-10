from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

GOOGLE_SHEETS_API_KEY=os.getenv("GOOGLE_SHEETS_API_KEY")
SPREADSHEET_ID=os.getenv("SPREADSHEET_ID")

apiurl = lambda x='': f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}{x}?key={GOOGLE_SHEETS_API_KEY}"

projects_list = {}

try:
    with open('projects_list','r+') as file:
        projects_list = json.loads(file.read())
except:
    pass

def updateprojects_list(data):
    with open('projects_list','w+') as file:
        file.write(json.dumps(data))

def listtojson(data):
    if data == []: return []
    
    header = data[0]
    rows = data[1:]

    json_data = list()

    for row in rows:
        row_dict = dict(zip(header, row))
        json_data.append(row_dict)
    
    return json_data

# @app.route('/')
# def home():
#     return "Hello, Suren!"

@app.route('/flush', methods=["GET"])
def clear():
    updateprojects_list({})

@app.route('/cache', methods=["GET"])
def cache():
    try: 
        response = requests.get(apiurl('/values/Projects!A2:B'))
        response.raise_for_status()
        for data in (response.json()).get("values",[]):
            projects_list[data[0]] = data[1]
        updateprojects_list(projects_list)

        # return  [name for name in projects_list.keys()]
        return  jsonify({"status": "ok"}),200
    
    except requests.exceptions.RequestException as e: 
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500
  

@app.route('/projectslist', methods=["GET"])
def projects():
    return list(projects_list.keys())


@app.route("/project/<name>",  methods=["GET"])
def fetchdata(name):
    try:
        if name not in projects_list:
            return jsonify({"message": "No project found"}), 404
        
        response = requests.get(apiurl(f'/values/{projects_list[name]}'))
        response.raise_for_status()
        
        return jsonify(listtojson((response.json()).get("values",[]))),200
    
    except requests.exceptions.RequestException as e: 
        return jsonify({"error": "Failed to fetch data", "details": str(e)}), 500
    

@app.route("/proxy/<url>", methods=["GET"])
def proxy(url):
    target_url = f'{url}'

    # Forward the request to the Superset server
    response = requests.request(
        method=request.method,
        url=target_url,
        headers=request.headers,
        params=request.args,
        data=request.data,
        cookies=request.cookies,
        allow_redirects=False,
    )

    # Create a response to send back to the client
    return Response(
        response.content,
        status=response.status_code,
        content_type=response.headers['Content-Type']
    )


if __name__ == '__main__':
    app.run(debug=True)
