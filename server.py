from flask import Flask
app = Flask(__name__)

@app.route("/static", methods=['GET'])
def paramedic_page():
    return app.send_static_file('static.html')

@app.route('/hello')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
