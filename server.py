from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import data_handler
import os
from forms import RegistrationForm, LoginForm



SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.split(SCRIPT_PATH)[0]
ANSWERS = os.path.join(SCRIPT_DIR, "sample_data/answer.csv")
QUESTIONS = os.path.join(SCRIPT_DIR, "sample_data/question.csv")
IMAGES = os.path.join(SCRIPT_DIR, "static/images")
app = Flask(__name__)
app.config['SECRET_KEY'] = '4bd54e4d2fc6f5e754931dadc9a39b0b'
bcrypt = Bcrypt(app)



@app.route("/", methods=['GET', 'POST'])
def index():
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True

    users = data_handler.get_users()
    latest_questions = data_handler.get_latest_questions()
    tags = data_handler.get_tag()
    question_tags = data_handler.get_question_tag()

    if request.method == 'POST':
        order = request.form.to_dict().get('sort')
        if order:
            latest_questions = data_handler.sort_questions(order)
        else:
            search_phrase = request.form.to_dict().get('searchbar')
            latest_questions = data_handler.search_for_question(search_phrase)

    return render_template('index.html', latest_questions=latest_questions, tags=tags, question_tags=question_tags,
                           logged_in=logged_in, user=user, users=users)


@app.route("/list", methods=['GET', 'POST'])
def hello():
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True

    users = data_handler.get_users()
    questions = data_handler.get_questions()
    tags = data_handler.get_tag()
    question_tags = data_handler.get_question_tag()
    search_phrase = None

    if request.method == 'POST':
        order = request.form.to_dict().get('sort')
        if order:
            questions = data_handler.sort_questions(order)
        else:
            search_phrase = request.form.to_dict().get('searchbar')
            questions = data_handler.search_for_question(search_phrase)

    return render_template('list.html', questions=questions, tags=tags, question_tags=question_tags,
                           search=search_phrase, logged_in=logged_in, user=user, users=users)


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if 'id' in session:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if request.method == 'POST' and request.form.to_dict().get('password') == request.form.to_dict().get('confirm_password'):
        user = request.form.to_dict()
        hashed_password = bcrypt.generate_password_hash(user.get('password')).decode('utf-8')
        # check for file uploads
        if request.files and request.files.to_dict()['image'].filename:
            image = request.files['image']
            image.filename = data_handler.create_image_id()
            app.config['IMAGE_UPLOADS'] = IMAGES
            app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['PNG', 'JPG']
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
            user['image'] = image.filename
        else:
            user['image'] = '2c5197c08bce2529'

        # register the user
        data_handler.registration(user, hashed_password)
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('index'))

    return  render_template('registration.html', title='Registration', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in session:
        return redirect(url_for('index'))

    form = LoginForm()
    if request.method == 'POST':
        user = request.form.to_dict()
        try:
            credentials = data_handler.login(user)[0]
        except:
            flash('Email or password incorrect.', 'error')
            return redirect(url_for('login'))

        hashed_password = credentials.get('password')
        confirmed = bcrypt.check_password_hash(hashed_password, user.get('password'))
        if confirmed:
            session['id'] = credentials.get('id')
            flash('You have been logged in.')
            return redirect(url_for('index'))
        else:
            flash('Please check email and password.', 'error')

    return render_template('login.html', title='Login', form=form)


@app.route('/user/<user_id>')
def user_page(user_id):
    logged_in = False
    user, current_user = None, None
    if 'id' in session:
        logged_in = True
        user = data_handler.get_user_account(user_id)[0]
        current_user = session['id']

        questions = data_handler.get_questions_for_user(user_id)
        answers = data_handler.get_answers_for_user(user_id)
        comments = data_handler.get_comments_for_user(user_id)
        return render_template('user_page.html', title='Account', logged_in=logged_in, user=user,
                               questions=questions, answers=answers, comments=comments, current_user=current_user)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    if 'id' not in session:
        return redirect(url_for('login'))

    session.pop('id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/tags')
def tags():
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True

    # get all the tags
    tags = data_handler.get_tag()
    # get the number of question for each tag
    question_count = data_handler.count_tags_by_genre()
    return render_template('tags.html', tags=tags, logged_in=logged_in, user=user, question_count=question_count)


@app.route('/tag/<tag_id>')
def selected_tag(tag_id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True

    questions_ids = [tag['question_id'] for tag in data_handler.get_question_tags(int(tag_id))]
    tag = data_handler.get_selected_tag(tag_id)[0]
    questions = data_handler.get_questions_by_tag(questions_ids)
    return render_template('selected_tag.html', tag=tag, questions=questions, logged_in=logged_in, user=user)


@app.route('/add-question', methods=['POST', 'GET'])
def add_question():
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # new question data
        question = {
            data_handler.QUESTION_HEADER[1]: data_handler.create_submission_time(),
            data_handler.QUESTION_HEADER[2]: 0,
            data_handler.QUESTION_HEADER[3]: 0,
            data_handler.QUESTION_HEADER[4]: request.form['title'],
            data_handler.QUESTION_HEADER[5]: request.form['message'],
            data_handler.QUESTION_HEADER[6]: ''
        }
        # check for file uploads
        if request.files and request.files.to_dict()['image'].filename:
            print('a')
            image = request.files['image']
            image.filename = data_handler.create_image_id()
            app.config['IMAGE_UPLOADS'] = IMAGES
            app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['PNG', 'JPG']
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
            question['image'] = image.filename
        # add question to database
        data_handler.add_question(question)
        # get the newly posted question (with id)
        new_question = data_handler.get_newly_posted_question(question.get('submission_time'))[0]
        # link question to user
        data_handler.link_question_to_user_on_post(user, new_question.get('id'))
        return redirect('/')

    return render_template('add_question.html', logged_in=logged_in, user=user)


@app.route('/question/<id>', methods=['POST', 'GET'])
def question(id):
    # initialize booleans
    accepted = False
    logged_in = False
    user_id = session.get('id', None)
    if 'id' in session:
        logged_in = True
    # get all the users to match with the questions
    users = data_handler.get_users()
    # get question and the comments for the question
    question = data_handler.get_single_question(id)[0]
    question_comments = data_handler.get_comments_for_question(id)
    # get answers and answer comment for the question
    answers = data_handler.get_answers_for_question_by_id(id)
    answer_id = data_handler.get_answer_id(answers)
    answer_comments = data_handler.get_comments_for_answer(answer_id)
    # get tags for the question
    tags = data_handler.get_tag()
    tag_id = data_handler.get_question_tag()
    # check for accepted state
    if request.method == 'POST':
        accepted = True
        submissioner = [user.get('id', None) for user in users if user.get('id', None) == question.get('user_id', None)][0]
        data_handler.flag_question(id, submissioner)
    # error handling for image path
    try:
        image_path = IMAGES + '/' + question['image']
        if len(image_path.split('/')[-1]) == 0:
            has_picture = False
        else:
            has_picture = os.path.exists(image_path)
    except:
        has_picture = False

    return render_template('question.html', question=question, answers=answers,
                            has_picture=has_picture, question_comments=question_comments,
                            answer_comments=answer_comments, tags=tags, tag_id=tag_id, logged_in=logged_in, user_id=user_id,
                            users=users, accepted=accepted)


@app.route('/question/<id>/delete_flag/', methods=['POST', 'GET'])
def delete_flag(id):
    if request.method == 'POST':
        # remove accepted state
        data_handler.remove_flag_from_question(id)
        return redirect(url_for('question', id=id))
    else:
        if 'id' in session:
            data_handler.remove_flag_from_question(id)
            return redirect(url_for('user_page', user_id=session['id']))
        else:
            flash('You need to login to access this feature')
            return redirect(url_for('login'))


@app.route('/question/<id>/new-comment', methods=['GET', 'POST'])
def comment_question(id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True

    if request.method == 'POST':
        # get new comment data
        question_comment = {
            'message': request.form.to_dict()['message'],
            'submission_time': data_handler.create_submission_time()
        }
        # write new comment to database
        data_handler.comment_question(question_comment, id)
        # get newly posted comment (with id)
        new_comment = data_handler.get_newly_posted_comment(question_comment.get('submission_time'))[0]
        # link comment to user
        data_handler.link_comment_to_user(user, new_comment.get('id'))
        return redirect(url_for('question', id=id))

    return render_template('comment_question.html', logged_in=logged_in, user=user)


@app.route('/question/<id>/new-answer', methods=['GET', 'POST'])
def post_answer(id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))
    # get question for answer
    question = data_handler.get_single_question(id)[0]
    if request.method == 'POST':
        # get new answer data
        answer = {
            data_handler.ANSWER_HEADER[1]: data_handler.create_submission_time(),
            data_handler.ANSWER_HEADER[2]: 0,
            data_handler.ANSWER_HEADER[3]: question['id'],
            data_handler.ANSWER_HEADER[4]: request.form['message'],
            data_handler.ANSWER_HEADER[5]: 0
        }
        # write new answer to database
        data_handler.post_answer(answer)
        # get the newly posted answer (with id)
        new_answer = data_handler.get_newly_posted_answer(answer.get('submission_time'))[0]
        # link new answer to user
        data_handler.link_answer_to_user(user, new_answer.get('id'))
        return redirect(url_for('question', id=id))

    return render_template('post-answer.html', question=question, logged_in=logged_in, user=user)


@app.route('/answer/<id>/<answer_id>/edit', methods=['GET', 'POST'])
def edit_answer(id, answer_id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    old_answer = data_handler.get_single_answer(answer_id)[0]
    if request.method == 'POST':
        new_answer = {
            'submission_time': data_handler.create_submission_time(),
            'message': request.form.to_dict()['edit_answer']
        }
        data_handler.edit_answer(new_answer, answer_id)

        return redirect(url_for('question', id=id))

    return render_template('edit_answer.html', old_answer=old_answer, logged_in=logged_in, user=user)


@app.route('/answer/delete/<id>/<answer_id>')
def delete_answer(id, answer_id):
    if 'id' not in session:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    data_handler.delete_comment_by_answer_id(answer_id)
    data_handler.delete_answer(answer_id)
    return redirect(url_for('question', id=id))


@app.route('/answer/<id>/<answer_id>/new-comment', methods=['GET', 'POST'])
def comment_answer(id, answer_id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # new comment data
        comment = {
            'submission_time': data_handler.create_submission_time(),
            'message': request.form.to_dict().get('message')
        }
        # insert comment into database
        data_handler.comment_answer(answer_id, comment)
        # get newly posted comment
        new_comment = data_handler.get_newly_posted_comment(comment.get('submission_time'))[0]
        # link new comment to user
        data_handler.link_comment_to_user(user, new_comment.get('id'))
        return redirect(url_for('question', id=id))

    return render_template('comment_answer.html', logged_in=logged_in, user=user)


@app.route('/comment/<id>/<comment_id>/edit', methods=['GET', 'POST'])
def edit_comment(id, comment_id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    old_question_comment = data_handler.get_single_comment(comment_id)[0]
    if request.method == 'POST':

        new_comment = {
            'submission_time': data_handler.create_submission_time(),
            'message': request.form.to_dict()['message']
        }
        data_handler.edit_comment(comment_id, new_comment)

        return redirect(url_for('question', id=id))

    return render_template('edit_comment.html', old_question_comment=old_question_comment, logged_in=logged_in, user=user)


@app.route('/comment/<id>/<comment_id>/delete')
def delete_comment(id, comment_id):
    if 'id' in session:
        logged_in = True
        data_handler.delete_comment(comment_id)
        return redirect(url_for('question', id=id))
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))


@app.route('/question/<id>/delete')
def delete_question(id):
    if 'id' in session:
        answers = data_handler.get_answers_for_question_by_id(id)
        answer_ids = [answer.get('id') for answer in answers]

        data_handler.delete_tag_by_question_id(id)
        data_handler.delete_question(id, answer_ids)
        return redirect('/list')
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))


@app.route('/question/<id>/edit', methods=['POST', 'GET'])
def edit_question(id):
    logged_in = False
    user = session.get('id', None)
    if 'id' in session:
        logged_in = True
    else:
        flash('Please sign in to post a question.', 'error')
        return redirect(url_for('login'))

    question = data_handler.get_single_question(id)[0]
    if request.method == 'POST':
        new_data = {
            data_handler.QUESTION_HEADER[0]: question['id'],
            data_handler.QUESTION_HEADER[1]: data_handler.create_submission_time(),
            data_handler.QUESTION_HEADER[2]: question['vote_number'],
            data_handler.QUESTION_HEADER[3]: question['view_number'],
            data_handler.QUESTION_HEADER[4]: request.form['title'],
            data_handler.QUESTION_HEADER[5]: request.form['message'],
            data_handler.QUESTION_HEADER[6]: ''
        }

        if request.files and request.files.to_dict()['image'].filename:
            image = request.files['image']
            image.filename = data_handler.create_image_id()
            app.config['IMAGE_UPLOADS'] = IMAGES
            app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['PNG', 'JPG']
            image.save(os.path.join(app.config['IMAGE_UPLOADS'], image.filename))
            new_data['image'] = image.filename

        data_handler.edit_question(id, new_data)
        return redirect(url_for('question', id=question['id']))

    return render_template('edit-question.html', question=question, logged_in=logged_in, user=user)


@app.route('/question/<id>/vote_up/<user_id>')
def vote_up(id, user_id):
    if 'id' in session:
        data_handler.edit_question_vote(id, vote_up=True)
        data_handler.update_user_reputation(user_id, like=True)
        return redirect(url_for('hello'))
    else:
        flash('You need to login to access this feature')
        return redirect(url_for('question', id=id))


@app.route('/question/<id>/vote_down/<user_id>')
def vote_down(id, user_id):
    if 'id' in session:
        data_handler.edit_question_vote(id, user_id)
        data_handler.update_user_reputation(user_id)
        return redirect(url_for('hello'))
    else:
        flash('You need to login to access this feature')
        return redirect(url_for('question', id=id))


@app.route('/answer/<id>/<answer_id>/vote_up/<user_id>')
def vote_up_answer(id, answer_id, user_id):
    if 'id' in session:
        question = data_handler.get_single_question(id)[0]
        data_handler.edit_answer_vote(answer_id, vote_up=True)
        data_handler.update_user_reputation_on_answer(user_id, like=True)
        return redirect(url_for('question', id=question['id']))
    else:
        flash('You need to login to access this feature')
        return redirect(url_for('question', id=id))


@app.route('/answer/<id>/<answer_id>/vote_down/<user_id>')
def vote_down_answer(id, answer_id, user_id):
    if 'id' in session:
        question = data_handler.get_single_question(id)[0]
        data_handler.edit_answer_vote(answer_id)
        data_handler.update_user_reputation_on_answer(user_id)
        return redirect(url_for('question', id=question['id']))
    else:
        flash('You need to login to access this feature')
        return redirect(url_for('question', id=id))


@app.route('/question/<id>/new-tag', methods=['GET', 'POST'])
def add_tag(id):
    if request.method == 'POST':
        tag = request.form.to_dict().get('tag')
        tag_id = data_handler.select_tag_id(tag)[0]['id']
        data_handler.add_tag(id, tag_id)
    return redirect(url_for('question', id=id))


@app.route('/question/<id>/<t_id>/delete-tag')
def delete_tag(id, t_id):
    data_handler.delete_tag(t_id, id)
    return redirect(url_for('question', id=id))


if __name__ == "__main__":
    app.run(
        debug=True,
        port=7500
    )
