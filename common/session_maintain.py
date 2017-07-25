'''
Holds the sqlite3 database related functions which validates
for the session hijacking and
MITM attacks, Man in the Middle Attacks

Params used to verify authenticity : User-Agent, User IP, Cookie
@Author : Vinay Ranjan
'''


import sqlite3


# global conn
# conn = sqlite3.connect('templates/common/user_sessions.db')


# def create_table():
#     try:
#         conn.execute('''CREATE TABLE session_table
#             (remote_ip TEXT NOT NULL,
#             cookie TEXT    NOT NULL,
#             user_agent TEXT NOT NULL);''')
#         return True
#     except:
#         pass

# # insert a new user to the session maintain table


# def insert_user(remote_ip, cookie, user_agent):
#     try:
#         conn.execute(
#             "INSERT INTO session_table VALUES ('%s', '%s', '%s')" %
#             (remote_ip, cookie, user_agent))
#         conn.commit()
#         return True
#     except:
#         return False

# # check the cookie whether it exists in the table or not


# def check_cookie_existance(cookie):
#     try:
#         _user_session = conn.execute(
#             "select count(*) from session_table where cookie = '%s'" %
#             (cookie))
#         num_rows = _user_session.fetchone()[0]
#         if num_rows > 0:
#             return True
#         else:
#             return False
#     except:
#         return False

# # re-auth user to check if the user is having same IP,
# # same browser and same cookie


# def re_auth_user(remote_ip, cookie, user_agent):
#     try:
#         _user_sessions_all = conn.execute(
#             "select count(*) from session_table where cookie = '%s'" %
#             (remote_ip, cookie, user_agent))
#         num_rows = _user_sessions_all.fetchone()[0]
#         if num_rows == 1:
#             return True
#         else:
#             return False
#     except:
#         return False

# # force clear the cookies if found to be not origional
# # using the above three parameters


# def checkout_user_cookie(handler, args):
#     handler.clear_cookie('user')
#     return handler.redirect(args.get('next', ['/'])[0])

# # this function needs to be called from all the
# # gramex templates and the index file


def avoid_session_hijacking(handler, args):
    # master_flag = True
    # try:
    #     create_table()
    # except:
    #     pass

    # if master_flag is True:
    #     remote_ip = handler.request.remote_ip or None
    #     cookie = handler.request.headers['Cookie'] or None
    #     user_agent = handler.request.headers['User-Agent'] or None
    #     try:
    #         if ((cookie is not None) & (cookie != '')):
    #             check_cookie_existance_flag = check_cookie_existance(cookie)

    #             if check_cookie_existance_flag is True:
    #                 re_auth_user_flag = re_auth_user(
    #                     remote_ip, cookie, user_agent)

    #                 if re_auth_user_flag is True:
    #                     pass

    #                 else:
    #                     print "checkout user cookie call"
    #                     checkout_user_cookie(handler, args)

    #             else:
    #                 insert_user(remote_ip, cookie, user_agent)
    #         else:
    #             pass
    #     except:
    #         pass

    # conn.close()
    return True


if __name__ == "__main__":
    pass
