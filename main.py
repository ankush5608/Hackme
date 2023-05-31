from __future__ import division
from fastapi import FastAPI, Depends, Request, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore, firestore_async
from google.cloud.firestore_v1.base_query import FieldFilter
# import os, typing
from api_globals import GlobalsMiddleware, g
import pandas as pd
from json import loads
import time

cred = credentials.Certificate('aventus-website.json')
firebase_admin.initialize_app(cred)

db = firestore.client()
# firebaseConfig = {
#   "apiKey": "AIzaSyBgT68Ra8QzLU6WkSgFTX0ws2Veupng7EE",
#   "authDomain": "test-aventus.firebaseapp.com",
#   "projectId": "test-aventus",
#   "storageBucket": "test-aventus.appspot.com",
#   "messagingSenderId": "330950556473",
#   "appId": "1:330950556473:web:03f5b5c3071c20a56546e8",
#   "measurementId": "G-0JVRVC3R7K"
# };

app = FastAPI()
api_router = APIRouter()
# api_router.include_router(login.router, prefix="", tags=["auth-webapp"])

allow_all = ['*']
app.add_middleware(GlobalsMiddleware)
app.add_middleware(
   CORSMiddleware,
   allow_origins=allow_all,
   allow_credentials=True,
   allow_methods=allow_all,
   allow_headers=allow_all
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



# def flash(request: Request, message: typing.Any, category: str = "primary") -> None:
#    if "_messages" not in request.session:
#        request.session["_messages"] = []
#        request.session["_messages"].append({"message": message, "category": category})
#
# def get_flashed_messages(request: Request):
#    print(request.session)
#    return request.session.pop("_messages") if "_messages" in request.session else []

# templates.env.globals['get_flashed_messages'] = get_flashed_messages

@app.on_event("startup")
async def load_data():
    g.df = pd.read_csv('teams.csv')

@app.get("/", dependencies=[Depends(load_data)], response_class=HTMLResponse)
async def home(request: Request):
    # return templates.TemplateResponse("home.html", {"request": request})
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/qr_scan/", dependencies=[Depends(load_data)], response_class=HTMLResponse)
async def add_entry(request: Request, uid: str):
    uid = uid.strip()
    print(f'"{uid}"')
    # Registered participants
    s = uid in g.df['UID'].tolist()
    if s:

        participants = "participants"
        cursor = db.collection(participants)
        # print(cursor.get()[1].to_dict())
        query = cursor.where(filter=FieldFilter("UID", "==", uid)).get()

        # query_len = list(query).__len__()

        data = query[0].to_dict()
        print(f'{query[0].id} => {data}')

        if data:                       # Check if uid in firestore
            print("Rendering checkin_checkout page...")
            # cursor.document(uid).update({'checkin': firestore.ArrayUnion([13.00])})
            # cursor.document(uid).update({'checkout': firestore.ArrayUnion([13.00])})
            # print(data['status'])
            # if data['status'] == 0:
            #     cursor.document(uid).update({'status': "IN"})
            # elif data['status'] == "IN":
            #     cursor.document(uid).update({'status': "OUT"})
            # elif data['status'] == 'OUT':
            #     cursor.document(uid).update({'status': "IN"})
            return templates.TemplateResponse('checkin_out.html', {'request': request, 'UID': uid, 'password': "aventus@6969"})

        details = g.df.loc[g.df['UID'] == uid].to_json(orient='records')
        doc = loads(details[1:-1])
        doc['status'] = "NULL"
        member_status = "UNREGISTERED"
        payload = {'request': request, 'Team Member': member_status, 'Details': doc}
        # db.collection(participants).document(uid).set(doc)
        return templates.TemplateResponse('master_checkin.html', payload)
        # cursor = db.collection(participants)
        # # query = cursor.where("UID", "in", ["jflksdjflk"]).stream()
        # query = cursor.where(filter=FieldFilter("UID", "in", [uid])).stream()
        # for doc in query:
        #     print(f'{doc.id} => {doc.to_dict()}')
    else:
        # Invalid
        return {'Error': 'INVALID UID FOUND'}


@app.post("/checkin_out/{uid}")
async def checkin_out(request: Request, uid: str):
    print(uid)
    # now = datetime.now()
    # entry_time = now.strftime("%d/%m/%Y %H:%M:%S ")
    entry_time = time.strftime("%d/%m/%Y %I:%M:%S %p", time.gmtime(time.time() + 19800))
    participants = "participants"
    cursor = db.collection(participants)
    query = cursor.where(filter=FieldFilter("UID", "==", uid)).get()
    status = query[0].to_dict()['status']
    print(status)
    if status == "NULL":
        print("Added status entry")
        cursor.document(uid).update({'status': "IN"})
        cursor.document(uid).update({'checkin': firestore.ArrayUnion([entry_time])})
    elif status == "IN":
        cursor.document(uid).update({'status': "OUT"})
        cursor.document(uid).update({'checkout': firestore.ArrayUnion([entry_time])})
    elif status == 'OUT':
        cursor.document(uid).update({'status': "IN"})
        cursor.document(uid).update({'checkin': firestore.ArrayUnion([entry_time])})
    else:
        print("wrong status")

    # return {"API": "called successfully"}
    # except:
    #     print("ERROR")
    #     return {"Internal Error": "Problem in the code"}

