from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return '<html><body><h1>Stinky :)</h1></body></html>'

if __name__ == '__main__':
    app.run()
