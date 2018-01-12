from flask import Flask, render_template, request
import pickle as pkl
app = Flask(__name__)
fb = pkl.load(open('data.pkl', 'rb'))



def format_for_search_result(person):
    monitored = {
        f.name() : f.username() for f in [fb.users[_] for _ in person.rev_friends]
        }
    return {'name': person.name(),
            'username': person.username(),
            'monitored': monitored
        }


@app.route('/')
def hello_world():
    return render_template('index.html',
        query="",
        results=[])


@app.route('/search')
def search_results(method='POST'):
    search = request.args.get('search')
    results = fb.search_user_names(search)
    results = [format_for_search_result(_) for _ in results]
    return render_template('index.html',
                           query=search,
                           results=results)


if __name__ == '__main__':
    app.run()