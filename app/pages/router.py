import os
import shutil
from typing import Optional

from fastapi import APIRouter, Request, Depends, status, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.datastructures import FormData

from app.utils import * # get_db, save_db, get_md5, find_user, update_user_profile

router = APIRouter(tags=['Frontend', 'Auth'])

templates = Jinja2Templates(directory='app/templates')

def get_current_user_login(request: Request) -> Optional[str]:
    return request.cookies.get("session_login")

# Главная страница
@router.get('/', response_class=HTMLResponse)
async def get_main_page(request: Request, current_user_login: Optional[str] = Depends(get_current_user_login)):
    users = get_db()
    
    context = {
        'request': request,
        'users': users,
        'current_user_login': current_user_login
    }
    return templates.TemplateResponse(name='index.html', context=context)

# Аутентификация
@router.get('/auth', response_class=HTMLResponse)
async def get_auth_page(request: Request):
    return templates.TemplateResponse(name='auth.html', context={'request': request, 'error': None})

@router.post('/auth')
async def handle_auth(request: Request):
    data: FormData = await request.form()
    action = data.get('action')
    login = data.get('login')
    password = data.get('password')
    name = data.get('name')
        
    if ' ' in password:
        error = "Пароль не должен содержать пробелов."
        return templates.TemplateResponse(name='auth.html', context={'request': request, 'error': error})

    password_md5 = get_md5(password)
    
    if action == 'register':
        if find_user(login):
            error = "Пользователь с таким логином уже существует."
            return templates.TemplateResponse(name='auth.html', context={'request': request, 'error': error})
            
        # Регистрация
        new_user = {
            "name": name or login,
            "login": login,
            "password_md5": password_md5,
            "message": "Привет! Я только что зарегистрировался.",
            "photo": "default.png"
        }
        users = get_db()
        users.append(new_user)
        save_db(users)
        
        response = RedirectResponse(url='/profile', status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session_login", value=login)
        return response
        
    elif action == 'login':
        user = find_user(login)
        if user and user['password_md5'] == password_md5:
            # Успешный вход
            response = RedirectResponse(url='/profile', status_code=status.HTTP_302_FOUND)
            response.set_cookie(key="session_login", value=login)
            return response
        else:
            error = "Неверный логин или пароль."
            return templates.TemplateResponse(name='auth.html', context={'request': request, 'error': error})

# Профиль
@router.get('/profile', response_class=HTMLResponse)
async def get_profile_page(request: Request, current_user_login: str = Depends(get_current_user_login)):
    if not current_user_login:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    user = find_user(current_user_login)
    if not user:
        response = RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session_login")
        return response

    context = {'request': request, 'user': user, 'error': None}
    return templates.TemplateResponse(name='profile.html', context=context)


@router.post('/profile')
async def update_profile(
    request: Request, 
    current_user_login: str = Depends(get_current_user_login),
    message: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    if not current_user_login:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
        
    user = find_user(current_user_login)
    context = {'request': request, 'user': user, 'error': None}
    new_photo_filename = user['photo']

    if photo and photo.filename:
        _, ext = os.path.splitext(photo.filename)
        allowed_extensions = {'.png', '.jpg', '.jpeg'}
        
        if ext.lower() in allowed_extensions:
            new_photo_filename = f"{current_user_login}_{os.urandom(8).hex()}{ext.lower()}"
            file_path = f"app/images/{new_photo_filename}"
            
            if user['photo'] != "default.png" and os.path.exists(f"app/images/{user['photo']}"):
                os.remove(f"app/images/{user['photo']}")
                
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
        else:
            context['error'] = "Недопустимый формат файла. Разрешены только PNG, JPG, JPEG."
            return templates.TemplateResponse(name='profile.html', context=context)

    update_user_profile(
        login=current_user_login,
        message=message if message is not None else user['message'],
        photo=new_photo_filename
    )
    
    user = find_user(current_user_login)
    context['user'] = user
    context['message'] = "Профиль успешно обновлен!"
    return templates.TemplateResponse(name='profile.html', context=context)

# Удаление учётной записи
@router.post('/profile/delete')
async def delete_profile(current_user_login: str = Depends(get_current_user_login)):
    if not current_user_login:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    deleted_user = delete_user(current_user_login)

    if deleted_user:
        photo_path = f"app/images/{deleted_user['photo']}"
        if deleted_user['photo'] != "default.png" and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception as e:
                print(f"Ошибка при удалении фото: {e}")

    response = RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_login")
    return response

# Выход
@router.get('/logout')
async def logout():
    response = RedirectResponse(url='/', status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_login")
    return response