import datetime
import time
import database
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from typing import List, Dict


FILE_PATH = '/sample_data/questions.csv'
QUESTION_HEADER = ['id', 'submission_time', 'view_number', 'vote_number', 'title', 'message', 'image']
ANSWER_HEADER = ['id', 'submission_time', 'vote_number', 'question_id', 'message', 'image']
Q_PICTURE = 'static/images/question_images'


@database.connection_handler
def registration(cursor: RealDictCursor, user, hashed_password):
    query = """
        INSERT INTO users (first_name, last_name, created, password, email, username, image)
        VALUES (%(first_name)s, %(last_name)s, %(created)s, %(password)s, %(email)s, %(username)s, %(image)s)
    """
    cursor.execute(query, {'first_name': user.get('first_name'), 'last_name': user.get('last_name'),
                           'created': create_submission_time(), 'password': hashed_password,
                           'email': user.get('email'), 'username': user.get('username'), 'image': user.get('image')})
    return None


@database.connection_handler
def login(cursur: RealDictCursor, user):
    query = """
        SELECT *
        FROM users
        WHERE email = %(email)s
    """
    cursur.execute(query, {'email': user.get('email')})
    return cursur.fetchall()


@database.connection_handler
def get_user_account(cursor: RealDictCursor, user_id):
    query = """
        SELECT *
        FROM users
        WHERE id = %(user_id)s
    """
    cursor.execute(query, {'user_id': user_id})
    return cursor.fetchall()


@database.connection_handler
def flag_question(cursor: RealDictCursor, question_id, submissioner):
    question_query = """
        UPDATE question
        SET accepted = true
        WHERE id = %(question_id)s
    """
    cursor.execute(question_query, {'question_id': question_id})
    # update reputation
    user_query = """
        UPDATE users
        SET reputation = reputation + 15
        WHERE id = %(submissioner)s
    """
    cursor.execute(user_query, {'submissioner': submissioner})
    return None


@database.connection_handler
def remove_flag_from_question(cursor: RealDictCursor, question_id):
    question_query = """
        UPDATE question
        SET accepted = false 
        WHERE id = %(question_id)s
    """
    cursor.execute(question_query, {'question_id': question_id})
    return None


@database.connection_handler
def get_questions_for_user(cursor: RealDictCursor, id):
    query = """
        SELECT *
        FROM question
        WHERE user_id = %(id)s
    """
    cursor.execute(query, {'id': id})
    return cursor.fetchall()


@database.connection_handler
def get_answers_for_user(cursor: RealDictCursor, id):
    query = """
        SELECT *
        FROM answer
        WHERE user_id = %(id)s
    """
    cursor.execute(query, {'id': id})
    return cursor.fetchall()


@database.connection_handler
def get_comments_for_user(cursor: RealDictCursor, id):
    query = """
        SELECT *
        FROM comment
        WHERE user_id = %(id)s
    """
    cursor.execute(query, {'id': id})
    return cursor.fetchall()


@database.connection_handler
def get_questions(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM question
        ORDER BY submission_time
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def get_users(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM users
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def link_question_to_user_on_post(cursor: RealDictCursor, account, question_id):
    query = """
        UPDATE question
        SET user_id = %(account)s
        WHERE id = %(question_id)s
    """
    cursor.execute(query, {'account': int(account), 'question_id': int(question_id)})
    return None


@database.connection_handler
def link_answer_to_user(cursor: RealDictCursor, user_id, answer_id):
    query = """
        UPDATE answer
        SET user_id = %(user_id)s
        WHERE id = %(answer_id)s
    """
    cursor.execute(query, {'user_id': user_id, 'answer_id': answer_id})
    return None


@database.connection_handler
def link_comment_to_user(cursor: RealDictCursor, user_id, comment_id):
    query = """
        UPDATE comment
        SET user_id = %(user_id)s
        WHERE id = %(comment_id)s
    """
    cursor.execute(query, {'user_id': user_id, 'comment_id': comment_id})
    return None


@database.connection_handler
def get_newly_posted_question(cursor: RealDictCursor, submission_time):
    query = """
        SELECT *
        FROM question
        WHERE submission_time = %(submission_time)s
    """
    cursor.execute(query, {'submission_time': submission_time})
    return cursor.fetchall()


@database.connection_handler
def get_newly_posted_answer(cursor: RealDictCursor, submission_time):
    query = """
        SELECT * 
        FROM answer
        WHERE submission_time = %(submission_time)s
    """
    cursor.execute(query, {'submission_time': submission_time})
    return cursor.fetchall()


@database.connection_handler
def get_newly_posted_comment(cursor: RealDictCursor, submission_time):
    query = """
        SELECT *
        FROM comment
        WHERE submission_time = %(submission_time)s
    """
    cursor.execute(query, {'submission_time': submission_time})
    return cursor.fetchall()


@database.connection_handler
def get_latest_questions(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM question
        ORDER BY submission_time DESC 
        LIMIT 5;
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def get_question_tags(cursor:RealDictCursor, tag_id):
    query = """
        SELECT * 
        FROM question_tag
        WHERE tag_id = %(tag_id)s
    """
    cursor.execute(query, {'tag_id': tag_id})
    return cursor.fetchall()


@database.connection_handler
def get_questions_by_tag(cursor:RealDictCursor, question_id):
    query = """
        SELECT *
        FROM question
        WHERE id = ANY (%s)
    """
    cursor.execute(query, (question_id,))
    return cursor.fetchall()


@database.connection_handler
def get_single_question(cursor: RealDictCursor, question_id):
    query = """
        SELECT *
        FROM question
        WHERE id = %(question_id)s
    """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchall()


@database.connection_handler
def get_answers_for_question_by_id(cursor: RealDictCursor, id):
    query = """
        SELECT *
        FROM answer
        WHERE question_id = %(id)s
        ORDER BY vote_number DESC 
    """
    cursor.execute(query, {'id': id})
    return cursor.fetchall()


@database.connection_handler
def get_single_answer(cursor: RealDictCursor, answer_id):
    query = """
        SELECT *
        FROM answer
        WHERE id = %(answer_id)s
    """
    cursor.execute(query, {'answer_id': answer_id})
    return cursor.fetchall()


@database.connection_handler
def add_question(cursor: RealDictCursor, question):
    query = """
        INSERT INTO question (submission_time, view_number, vote_number, title, message, image) 
        VALUES (%(submission_time)s, %(view_number)s, %(vote_number)s, %(title)s, %(message)s, %(image)s) 
    """
    cursor.execute(query, {'submission_time': question['submission_time'], 'view_number': question['view_number'],
                           'vote_number': question['vote_number'], 'title': question['title'],
                           'message': question['message'], 'image': question['image']})
    return None


@database.connection_handler
def post_answer(cursor: RealDictCursor, answer):
    query = """
        INSERT INTO answer (submission_time, vote_number, question_id, message, image) 
        VALUES (%(submission_time)s, %(vote_number)s, %(question_id)s, %(message)s, %(image)s)
    """
    cursor.execute(query, {'submission_time': answer['submission_time'], 'vote_number': answer['vote_number'],
                           'question_id': answer['question_id'], 'message': answer['message'], 'image': answer['image']})
    return None


@database.connection_handler
def delete_answer(cursor: RealDictCursor, answer_id):
    query = """
        DELETE FROM answer
        WHERE id = %(answer_id)s
    """
    cursor.execute(query, {'answer_id': answer_id})
    return None


@database.connection_handler
def delete_question(cursor: RealDictCursor, question_id, answer_ids):
    # delete corresponding answer comments
    answer_comment_query = """
        DELETE FROM comment
        WHERE answer_id = ANY (%s)
    """
    cursor.execute(answer_comment_query, (answer_ids,))
    # delete corresponding answers
    answer_query = """
        DELETE FROM answer
        WHERE id = ANY (%s)
    """
    cursor.execute(answer_query, (answer_ids,))
    # delete corresponding question comments
    question_comment_query = """
        DELETE FROM comment
        WHERE question_id = %(question_id)s
    """
    cursor.execute(question_comment_query, {'question_id': question_id})
    # delete corresponding answers
    answer_query = """
            DELETE FROM answer
            WHERE question_id = %(question_id)s
        """
    cursor.execute(answer_query, {'question_id': question_id})
    # delete question
    question_query = """
        DELETE FROM question
        WHERE id = %(question_id)s
    """
    cursor.execute(question_query, {'question_id': question_id})
    return None


@database.connection_handler
def edit_question(cursor: RealDictCursor, question_id, new_question):
    query = """
        UPDATE question
        SET title = %(title)s, message = %(message)s, image = %(image)s
        WHERE id = %(question_id)s
    """
    cursor.execute(query, {'question_id': question_id, 'title': new_question['title'],
                           'message': new_question['message'], 'image': new_question['image']})
    return None


@database.connection_handler
def edit_answer(cursor: RealDictCursor, new_answer, answer_id):
    query = """
        UPDATE answer
        SET submission_time = %(submission_time)s,
            message = %(message)s
        WHERE id = %(answer_id)s
    """
    cursor.execute(query, {'submission_time': new_answer.get('submission_time'),
                           'message': new_answer.get('message'), 'answer_id': answer_id})
    return None


@database.connection_handler
def edit_question_vote(cursor: RealDictCursor, q_id, vote_up=False):
    if vote_up:
        query = """
            UPDATE question
            SET vote_number = vote_number + 1
            WHERE id = %(q_id)s
        """
        cursor.execute(query, {'q_id': q_id})
    else:
        query = """
                    UPDATE question
                    SET vote_number = vote_number - 1
                    WHERE id = %(q_id)s
                """
        cursor.execute(query, {'q_id': q_id})
    return None


@database.connection_handler
def update_user_reputation(cursor: RealDictCursor, user_id, like=False):
    if like:
        query = """
            UPDATE users
            SET reputation = reputation + 5
            WHERE id = %(user_id)s
        """
        cursor.execute(query, {'user_id': user_id})
        return None
    else:
        query = """
            UPDATE users
            SET reputation = reputation - 2
            WHERE id = %(user_id)s
        """
        cursor.execute(query, {'user_id': user_id})
        return None


@database.connection_handler
def edit_answer_vote(cursor: RealDictCursor, answer_id, vote_up=False):
    if vote_up:
        query = """
            UPDATE answer
            SET vote_number = vote_number + 1
            WHERE id = %(answer_id)s
        """
    else:
        query = """
                    UPDATE answer
                    SET vote_number = vote_number - 1
                    WHERE id = %(answer_id)s
                """
    cursor.execute(query, {'answer_id': answer_id})
    return None


@database.connection_handler
def update_user_reputation_on_answer(cursor: RealDictCursor, user_id, like=False):
    if like:
        query = """
            UPDATE users
            SET reputation = reputation + 10
            WHERE id = %(user_id)s
        """
        cursor.execute(query, {'user_id': user_id})
        return None
    else:
        query = """
            UPDATE users
            SET reputation = reputation - 2
            WHERE id = %(user_id)s
        """
        cursor.execute(query, {'user_id': user_id})
        return None


@database.connection_handler
def get_comments_for_question(cursor: RealDictCursor, question_id):
    query = """
        SELECT id, question_id, answer_id, message, submission_time
        FROM comment
        WHERE question_id = %(question_id)s
        ORDER BY id
    """
    cursor.execute(query, {'question_id': question_id})
    return cursor.fetchall()


@database.connection_handler
def get_comments_for_answer(cursor: RealDictCursor, answer_id):
    query = """
        SELECT id, submission_time, message, answer_id
        FROM comment
        WHERE answer_id = ANY (%s)
    """
    cursor.execute(query, (answer_id,))
    return cursor.fetchall()


@database.connection_handler
def comment_question(cursor: RealDictCursor, comment, question_id):
    query = """
        INSERT INTO comment (question_id, answer_id, message, submission_time, edited_count)
        VALUES (%(question_id)s, NULL, %(message)s, %(submission_time)s, NULL)
    """
    cursor.execute(query, {'question_id': question_id, 'message': comment['message'],
                           'submission_time': comment['submission_time']})
    return None


@database.connection_handler
def edit_comment(cursor: RealDictCursor, comment_id, new_comment, answer=False):
    if answer:
        pass
    else:
        query = """
            UPDATE comment
            SET submission_time = %(submission_time)s,
                message = %(message)s
            WHERE id = %(comment_id)s
        """
    cursor.execute(query, {'comment_id': comment_id, 'message': new_comment.get('message'),
                           'submission_time': new_comment.get('submission_time')})
    return None


@database.connection_handler
def get_single_comment(cursor: RealDictCursor, comment_id):
    query = """
        SELECT * 
        FROM comment
        WHERE id = %(comment_id)s
    """
    cursor.execute(query, {'comment_id': comment_id})
    return cursor.fetchall()


@database.connection_handler
def delete_comment(cursor: RealDictCursor, comment_id):
    query = """
        DELETE FROM comment
        WHERE id = %(comment_id)s
    """
    cursor.execute(query, {'comment_id': int(comment_id)})
    return None


@database.connection_handler
def delete_comment_by_answer_id(cursor: RealDictCursor, answer_id):
    query = """
        DELETE FROM comment
        WHERE answer_id = %(answer_id)s
    """
    cursor.execute(query, {'answer_id': answer_id})
    return None


@database.connection_handler
def comment_answer(cursor: RealDictCursor, answer_id, comment):
    query = """
     INSERT INTO comment (question_id, answer_id, message, submission_time, edited_count)
     VALUES (NULL, %(answer_id)s, %(message)s, %(submission_time)s, NULL)
    """
    cursor.execute(query, {'answer_id': answer_id, 'message': comment.get('message', None),
                           'submission_time': comment.get('submission_time', None)})
    return None


@database.connection_handler
def sort_questions(cursor: RealDictCursor, order):
    query = """
        SELECT submission_time, view_number, vote_number, title, message, id, image
        FROM question
        ORDER BY {order} DESC 
    """.format(order=order)
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def search_for_question(cursor: RealDictCursor, search_phrase):
    query = """
        SELECT *
        FROM question
        WHERE LOWER(title) LIKE LOWER(%(search_phrase)s)
                    OR LOWER (message) LIKE LOWER (%(search_phrase)s);
    """
    cursor.execute(query, {'search_phrase': '%' + search_phrase + '%'})
    return cursor.fetchall()


@database.connection_handler
def get_tag(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM tag
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def get_selected_tag(cursor: RealDictCursor, tag_id):
    query = """
        SELECT *
        FROM tag
        WHERE id = %(tag_id)s
    """
    cursor.execute(query, {'tag_id': tag_id})
    return cursor.fetchall()


@database.connection_handler
def count_tags_by_genre(cursor: RealDictCursor):
    query = """
        SELECT name, COUNT(tag_id)
        FROM tag
        JOIN question_tag
        ON tag.id = question_tag.tag_id
        GROUP BY name
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def get_question_tag(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM question_tag
    """
    cursor.execute(query)
    return cursor.fetchall()


@database.connection_handler
def select_tag_id(cursor: RealDictCursor, tag_name):
    query = """
        SELECT *
        FROM tag
        WHERE name = %(tag_name)s
    """
    cursor.execute(query, {'tag_name': tag_name})
    return cursor.fetchall()


@database.connection_handler
def add_tag(cursor: RealDictCursor, question_id, tag_id):
    query = """
        INSERT INTO question_tag
        VALUES (%(question_id)s, %(tag_id)s)
    """
    cursor.execute(query, {'question_id': question_id, 'tag_id': tag_id})
    return None


@database.connection_handler
def delete_tag(cursor: RealDictCursor, tag_id, question_id):
    query = """
        DELETE FROM question_tag
        WHERE tag_id = %(tag_id)s
        AND question_id = %(question_id)s
    """
    cursor.execute(query, {'tag_id': tag_id, 'question_id': question_id})
    return None


@database.connection_handler
def delete_tag_by_question_id(cursor: RealDictCursor, question_id):
    query = """
        DELETE FROM question_tag
        WHERE question_id = %(question_id)s
    """
    cursor.execute(query, {'question_id': question_id})
    return None


def create_submission_time():
    timestamp = int(time.time())
    submission_time = datetime.datetime.fromtimestamp(timestamp)
    return submission_time.strftime('%Y-%m-%d %H:%M')


def get_answer_id(answers):
    answer_id = [answer['id'] for answer in answers]
    return answer_id


def create_image_id():
    return secrets.token_hex(8)

