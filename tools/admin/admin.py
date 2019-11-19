from quart import Quart, abort, redirect, render_template, request, session, url_for
from config import MOD_COOKIES
from ..handlers import cookie_check

admin = Quart(__name__)

# @cookie_check(MOD_COOKIES)
@admin.route('/')
async def admin_main():
    state = admin.config['state']
    req = request.headers.get("Cookie")
    return await render_template('main.html', state=state)

# @cookie_check(MOD_COOKIES)
@admin.route('/manage', methods=['POST'])
async def admin_user_manage():
    state = admin.config['state']
    table = admin.config['table']
    form = await request.form
    print(form)
    action = form.get('action')
    if action is not None or action is not "":
        if action == 'ban':
            await table.route_json({"action" : "apply", "mod" : "trash", "userid" : form.get('userid')})
            return await render_template('main.html', state=state, message="Action effectuée")
    
    
