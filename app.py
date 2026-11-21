import os, uuid, hmac
import streamlit as st
import folium
from streamlit_folium import st_folium
from supabase import create_client
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='AquaWatch', page_icon='💧')
st.title('💧 AquaWatch')
st.caption('Water Leakage Complaint Management System')
def setting(k):
    try: return os.getenv(k) or st.secrets.get(k,'')
    except Exception: return os.getenv(k,'')
url, key, password = (setting(k) for k in ('SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','ADMIN_PASSWORD'))
st.write("Supabase URL configured:", bool(url))
st.write("Supabase key configured:", bool(key))
if not url or not key:
    st.error('Configure Supabase credentials first. Read README.md.'); st.stop()
@st.cache_resource
def connect(u,k): return create_client(u,k)
sb=connect(url,key)
def show(c):
    st.write('**ID:**',c['id']); st.write('**Location:**',c['location']); st.write('**Description:**',c['description']); st.write('**Status:**',c['status'])
    if c.get('latitude') is not None and c.get('longitude') is not None:
        lat,lon=float(c['latitude']),float(c['longitude'])
        st.map([{'lat':lat,'lon':lon}],zoom=16)
        st.link_button('📍 Open exact pin in Google Maps',f'https://www.google.com/maps?q={lat},{lon}')
    if c.get('photo_path'):
        try:
            signed=sb.storage.from_('complaint-photos').create_signed_url(c['photo_path'],600)
            st.image(signed.get('signedURL') or signed.get('signedUrl'),width=400)
        except Exception: st.caption('Photo unavailable')
report,track,admin=st.tabs(['📝 Report Leakage','🔎 Track Complaint','🔐 Admin Dashboard'])
with report:
    st.subheader('📍 Mark the exact leakage location')
    st.caption('Move/zoom the map and CLICK the leakage spot. The pin is the reported location, not automatic GPS.')
    if 'pin' not in st.session_state: st.session_state.pin=None
    center=st.session_state.pin or {'lat':12.9716,'lng':77.5946}  # initial view: Bengaluru; pan anywhere
    m=folium.Map(location=[center['lat'],center['lng']],zoom_start=13,control_scale=True)
    if st.session_state.pin:
        folium.Marker([center['lat'],center['lng']],tooltip='Leakage location',icon=folium.Icon(color='red')).add_to(m)
    map_result=st_folium(m,height=380,width=None,key='leakage_map',returned_objects=['last_clicked'])
    if map_result and map_result.get('last_clicked'):
        st.session_state.pin=map_result['last_clicked']
    if st.session_state.pin:
        lat,lon=st.session_state.pin['lat'],st.session_state.pin['lng']
        st.success(f'Selected pin: {lat:.6f}, {lon:.6f}')
        st.markdown(f'[View pin in Google Maps](https://www.google.com/maps?q={lat},{lon})')
    else:
        st.info('Click on the map to mark where the leakage is happening.')
    with st.form('report',clear_on_submit=True):
        location=st.text_input('Location / landmark',max_chars=200)
        description=st.text_area('Describe the leakage',max_chars=2000)
        photo=st.file_uploader('Photo (optional, max 5 MB)',type=['jpg','jpeg','png'])
        submit=st.form_submit_button('Submit complaint')
    if submit:
        if not location.strip() or not description.strip(): st.warning('Enter location and description')
        elif not st.session_state.pin: st.warning('Click the leakage location on the map first')
        elif photo and photo.size>5*1024*1024: st.warning('Photo too large')
        else:
            cid=str(uuid.uuid4()); path=None
            try:
                if photo:
                    ext=photo.name.rsplit('.',1)[-1].lower(); path=f'{cid}.{ext}'
                    sb.storage.from_('complaint-photos').upload(path,photo.getvalue(),file_options={'content-type':'image/png' if ext=='png' else 'image/jpeg'})
                sb.table('complaints').insert({'id':cid,'location':location.strip(),'description':description.strip(),'status':'Pending','photo_path':path,'latitude':st.session_state.pin['lat'],'longitude':st.session_state.pin['lng']}).execute()
                st.success('Complaint submitted!'); st.code(cid); st.session_state.pin=None
            except Exception as e:
    if path:
        try:
            sb.storage.from_('complaint-photos').remove([path])
        except Exception:
            pass
    st.error(f'Could not save complaint: {e}')
with track:
    cid=st.text_input('Complaint tracking ID')
    if st.button('Track status'):
        try:
            cid=str(uuid.UUID(cid.strip()))
            data=sb.table('complaints').select('*').eq('id',cid).limit(1).execute().data
            if data: show(data[0])
            else: st.warning('Complaint not found')
        except ValueError: st.warning('Enter a valid ID')
        except Exception: st.error('Unable to retrieve complaint')
with admin:
    if not password: st.warning('Set ADMIN_PASSWORD to enable admin access')
    else:
        if not st.session_state.get('admin',False):
            guess=st.text_input('Admin password',type='password')
            if st.button('Log in'):
                if hmac.compare_digest(guess,password): st.session_state.admin=True; st.rerun()
                else: st.error('Wrong password')
        else:
            if st.button('Log out'): st.session_state.admin=False; st.rerun()
            try:
                data=sb.table('complaints').select('*').order('created_at',desc=True).limit(500).execute().data or []
                a,b,c=st.columns(3); a.metric('Total (latest 500)',len(data)); b.metric('Pending',sum(x['status']=='Pending' for x in data)); c.metric('Resolved',sum(x['status']=='Resolved' for x in data))
                for item in data:
                    with st.expander(f"{item['location']} — {item['status']} — {item['id'][:8]}"):
                        show(item)
                        statuses=['Pending','In Progress','Resolved']
                        status=st.selectbox('New status',statuses,index=statuses.index(item['status']),key=item['id'])
                        if st.button('Save status',key='save'+item['id']):
                            sb.table('complaints').update({'status':status}).eq('id',item['id']).execute(); st.success('Updated'); st.rerun()
            except Exception: st.error('Unable to load or update complaints')
