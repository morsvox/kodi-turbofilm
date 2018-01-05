#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, urllib2, cookielib, re, string, os, httplib, socket, urlparse
import base64
import random
import hashlib
import xml.etree.ElementTree as ET
from string import maketrans
import xbmcaddon, xbmc, xbmcgui, xbmcplugin


__settings__ = xbmcaddon.Addon(id='plugin.video.turbik.tv')
__language__ = __settings__.getLocalizedString
USERNAME = __settings__.getSetting('username')
USERPASS = __settings__.getSetting('password')
VIDEO_LANG = __settings__.getSetting('language') or 'en'
VIDEO_QUALITY = __settings__.getSetting('quality') or 'lq'
handle = int(sys.argv[1])

PLUGIN_NAME = 'turbik.tv'
SITE_HOSTNAME = 'turbik.tv'
SITEPREF = 'https://%s' % SITE_HOSTNAME
SITE_URL = SITEPREF + '/'

phpsessid_file = os.path.join(xbmc.translatePath('special://temp/'), 'plugin_video_turbiktv.sess')
plotdescr_file = os.path.join(xbmc.translatePath('special://temp/'), 'plugin_video_turbiktv.plot')
thumb = os.path.join(os.getcwd(), "icon.png")


def run_once():
    global USERNAME, USERPASS
    while (read_url('/') == None):
        user_keyboard = xbmc.Keyboard()
        user_keyboard.setHeading(__language__(30001))
        user_keyboard.doModal()
        if (user_keyboard.isConfirmed()):
            USERNAME = user_keyboard.getText()
            pass_keyboard = xbmc.Keyboard()
            pass_keyboard.setHeading(__language__(30002))
            pass_keyboard.setHiddenInput(True)
            pass_keyboard.doModal()
            if (pass_keyboard.isConfirmed()):
                USERPASS = pass_keyboard.getText()
                __settings__.setSetting('username', USERNAME)
                __settings__.setSetting('password', USERPASS)
            else:
                return False
        else:
            return False
    return True


def regex_or_default(text, pattern, default, flags=0):
    match = re.search(pattern, text, flags)
    xbmc.log('***** Matcher = %s' % match)
    return match.group(1) if match else default


def read_url(url, ref=None):
    use_auth = False
    inter = 2
    while inter:
        wurl = urlparse.urljoin(SITEPREF, url)
        cj = cookielib.CookieJar()
        h  = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(h)
        urllib2.install_opener(opener)
        post = None
        if use_auth:
            post = urllib.urlencode({'login': USERNAME, 'passwd': USERPASS})
            url = SITE_URL
        request = urllib2.Request(wurl, post)
        request.add_header('User-Agent', 'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.6.30 Version/10.70')
        request.add_header('Host', SITE_HOSTNAME)
        request.add_header('Accept', 'text/html, application/xml, application/xhtml+xml, */*')
        request.add_header('Accept-Language', 'ru,en;q=0.9')
        if ref != None:
            request.add_header('Referer', ref)
        if (os.path.isfile(phpsessid_file) and (not use_auth)):
            fh = open(phpsessid_file, 'r')
            phpsessid = fh.read()
            fh.close()
            request.add_header('Cookie', 'IAS_ID=' + phpsessid)
        o = urllib2.urlopen(request)
        for index, cookie in enumerate(cj):
            cookraw = re.compile('<Cookie IAS_ID=(.*?) for.*/>').findall(str(cookie))
            if len(cookraw) > 0:
                fh = open(phpsessid_file, 'w')
                fh.write(cookraw[0])
                fh.close()
        http = o.read()
        o.close()
        if (http.find('<div class="loginblock" id="loginblock">') == -1):
            return http
        else:
            use_auth = True
            url = '/Signin/'
        inter = inter - 1
    return None


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param


def show_series(url):
    def make_small_thumb(url):
        return url.replace('s.jpg', '.png')

    def make_poster(url):
        return url.replace('s.jpg', 'ts.jpg')

    http = read_url(url)
    if http == None:
        xbmc.log('[%s] ShowSeries() Error 1: Not received data when opening URL=%s' % (PLUGIN_NAME, url))
        return
    #xbmc.log(http)

    raw1 = re.compile('<div id="series">(.*?)<div id="footer">', re.DOTALL).findall(http)
    if len(raw1) == 0:
        xbmc.log('[%s] ShowSeries() Error 2: r.e. not found it necessary elements. URL=%s' % (PLUGIN_NAME, url))
        xbmc.log(http)
        return

    #xbmc.log(raw1[0])

    raw2 = re.compile('\s<a href="(.*?)">\s(.*?)</a>', re.DOTALL).findall(raw1[0])
    if len(raw1) == 0:
        xbmc.log('[%s] ShowSeries() Error 3: r.e. not found it necessary elements. URL=%s' % (PLUGIN_NAME, url))
        xbmc.log(raw1[0])
        return

    for wurl, http2 in raw2:
        raw_img = re.compile('<img src="(.*?)".*/>').findall(http2)
        if len(raw_img) == 0:
            Thumb = thumb
        else:
            Thumb = urlparse.urljoin(SITEPREF, raw_img[0])
        raw_en = re.compile('<span class="serieslistboxen">(.*?)</span>').findall(http2)
        if len(raw_en) == 0:
            TitleEN = 'No title'
        else:
            TitleEN = raw_en[0]
        raw_ru = re.compile('<span class="serieslistboxru">(.*?)</span>').findall(http2)
        if len(raw_ru) == 0:
            TitleRU = 'No title'
        else:
            TitleRU = raw_ru[0]
        Descr = ''
        raw_des = re.compile('<span class="serieslistboxperstext">(.*?)</span>').findall(http2)
        if len(raw_des) != 0:
            for cur_des in raw_des:
                Descr = Descr + cur_des + '\n'
        raw_des2 = re.compile('<span class="serieslistboxdesc">(.*?)</span>').findall(http2)
        if len(raw_des2) > 0:
            Descr = Descr + raw_des2[0]

        xbmc.log('*** Series info: Thumb=%s; TitleEN=%s; TitleRU=%s; wurl=%s' % (Thumb, TitleEN, TitleRU, wurl))

        if VIDEO_LANG == 'ru':
            Title = '%s (%s)' % (TitleRU, TitleEN)
        elif VIDEO_LANG == 'en':
            Title = '%s' % TitleEN

        thumb = make_small_thumb(Thumb)
        fanart = make_poster(Thumb)
        listitem = xbmcgui.ListItem(Title, iconImage=Thumb, thumbnailImage=thumb)
        listitem.setInfo(type="video", infoLabels={
                "title": Title,
                "plot": Descr,
                #"foldername": TitleRU
            }
        )
        listitem.setArt({'thumb': thumb, 'poster': fanart, 'fanart': fanart})
        url = sys.argv[0] + '?mode=OpenSeries&url=' + urllib.quote_plus(wurl) \
            + '&title=' + urllib.quote_plus(Title)
        xbmcplugin.addDirectoryItem(handle, url, listitem, True)


def open_series(url, title):
    http = read_url(url, SITEPREF + '/Series/')
    if http == None:
        xbmc.log('[%s] open_series() Error 1: No data when opening URL=%s' % (PLUGIN_NAME, url), xbmc.LOGERROR)
        return

    raw_topimg = re.compile('<div class="topimgseries">\s*<img src="(.*?)"').findall(http)
    if len(raw_topimg) == 0:
        TopIMG = thumb
    else:
        TopIMG = urlparse.urljoin(SITEPREF, raw_topimg[0])

    raw1 = re.compile('<div class="sserieslistbox">(.*?)<div class="sseriesrightbox">', re.DOTALL).findall(http)
    if len(raw1) == 0:
        xbmc.log('[%s] open_series() Error 2: `sserieslistbox` element not found. URL=%s' % (PLUGIN_NAME, url), xbmc.LOGERROR)
        xbmc.log(http)
        return

    raw2 = re.compile('<a href="(.+?)">\s(.*?)</a>', re.DOTALL).findall(raw1[0])
    if len(raw1) == 0:
        xbmc.log('[%s] open_series() Error 3: <a> element not found. URL=%s' % (PLUGIN_NAME, url), xbmc.LOGERROR)
        xbmc.log(raw1[0])
        return

    for wurl, http2 in raw2:
        Thumb = regex_or_default(http2, u'<img src="(.*?)".*/>', TopIMG)
        TitleEN = regex_or_default(http2, u'<span class="sserieslistonetxten">(.*?)</span>', 'No title')
        TitleRU = regex_or_default(http2, u'<span class="sserieslistonetxtru">(.*?)</span>', 'No title')
        SeaNUM = regex_or_default(http2, u'<span class="sserieslistonetxtse">Сезон: (.*?)</span>', 'Season not specified')
        EpiNUM = regex_or_default(http2, '<span class="sserieslistonetxtep">Эпизод: (.*?)</span>', 'The episode is not specified')

        xbmc.log('*** Series info: Thumb=%s; TitleEN=%s; TitleRU=%s; SeaNUM=%s; EpiNUM=%s; wurl=%s' % (Thumb, TitleEN, TitleRU, SeaNUM, EpiNUM, wurl))

        if VIDEO_LANG == 'ru':
            Title = 'Episode %s: %s / %s' % (EpiNUM, TitleRU, TitleEN)
        elif VIDEO_LANG == 'en':
            Title = 'Episode %s: %s' % (EpiNUM, TitleEN)

        Descr = 'Season: %s\nEpisode: %s' % (SeaNUM, EpiNUM)

        listitem = xbmcgui.ListItem(Title, iconImage=Thumb, thumbnailImage=Thumb)
        listitem.setInfo(type="Video",
                         infoLabels={
                "title": Title,
                "tvshowtitle": title,
                "plot": "",
                "episode": EpiNUM,
                "season": SeaNUM,
                "VideoCodec": "h264"
            }
        )
        listitem.setProperty("Fanart_Image", Thumb)
        url = sys.argv[0] + '?mode=Watch&url=' + urllib.quote_plus(wurl) \
            + '&title=' + urllib.quote_plus(Title)
        xbmcplugin.addDirectoryItem(handle, url, listitem, False)

    raw3 = re.compile('<div class="seasonnum">(.*?)</div>', re.DOTALL).findall(http)
    if len(raw3) == 0:
        xbmc.log('[%s] open_series() Error 4: `seasonnum` not found. URL=%s' % (PLUGIN_NAME, url))
        xbmc.log(http)
        return

    raw4 = re.compile('<a href="(.*?)"><span class=".*">(.*?)</span></a>').findall(raw3[0])
    if len(raw4) == 0:
        xbmc.log('[%s] open_series() Error 5: Inner <a> element not found. URL=%s' % (PLUGIN_NAME, url))
        xbmc.log(raw3[0])
        return

    for row_url, row_name in raw4:
        xbmc.log('*** row_url  = %s' % row_url)
        xbmc.log('*** row_name = %s' % row_name)

        listitem = xbmcgui.ListItem(row_name, iconImage=TopIMG, thumbnailImage=TopIMG)
        listitem.setInfo(type="Video", infoLabels={
            "Title": row_name
            })
        url = sys.argv[0] + '?mode=OpenSeries&url=' + urllib.quote_plus(row_url) \
            + '&title=' + urllib.quote_plus(title + ' : ' + row_name)
        xbmcplugin.addDirectoryItem(handle, url, listitem, True)


def watch_episode(url, title, img):

    def meta_decoder(param1):
        xlat_in  = '2I0=3Q8V7XGMRUH41Z5DN6L9BW'
        xlat_out = 'xuYokngrmTwfdcesilytpbzaJv'
        transtab = maketrans(xlat_in + xlat_out, xlat_out + xlat_in)

        param1 = param1.replace('%2b', '+')
        param1 = param1.replace('%3d', '=')
        param1 = param1.replace('%2f', '/')
        param1 = param1.translate(transtab)
        return base64.b64decode(param1)

    http = read_url(url)
    if http == None:
        xbmc.log('[%s] watch_episode() Error 1: Not received data when opening URL=%s' % (PLUGIN_NAME, url))
        return

    raw1 = re.compile('<input type="hidden" id="metadata" value="(.*)" />').findall(http)
    if len(raw1) == 0:
        xbmc.log('[%s] watch_episode() Error 2: r.e. not found it necessary elements. URL=%s' % (PLUGIN_NAME, url))
        xbmc.log(http)
        return
    Metadata = raw1[0]

    Plot = 'No plot'
    raw2 = re.compile('<span class="textdesc">(.*?)</span>', re.DOTALL).findall(http)
    if len(raw2)> 0:
        Plot = raw2[0]

    eid = '0'
    raw3 = re.compile('<input type="hidden" id="eid" value="(.*?)" />').findall(http)
    if len(raw3) > 0:
        eid = raw3[0]

    pid = '0'
    raw4 = re.compile('<input type="hidden" id="pid" value="(.*?)" />').findall(http)
    if len(raw4) > 0:
        pid = raw4[0]

    sid = '0'
    raw5 = re.compile('<input type="hidden" id="sid" value="(.*?)" />').findall(http)
    if len(raw5) > 0:
        sid = raw5[0]

    epwatch = '0'
    raw6 = re.compile('<input type="hidden" id="epwatch" value="(.*?)" />').findall(http)
    if len(raw6) > 0:
        epwatch = raw6[0]

    sewatch = '0'
    raw7 = re.compile('<input type="hidden" id="sewatch" value="(.*?)" />').findall(http)
    if len(raw7) > 0:
        sewatch = raw7[0]

    h1 = '0'
    raw8 = re.compile('<input type="hidden" id="h1" value="(.*?)" />').findall(http)
    if len(raw8) > 0:
        h1 = raw8[0]

    Hash = '0'
    raw9 = re.compile('<input type="hidden" id="hash" value="(.*?)" />').findall(http)
    if len(raw9) > 0:
        Hash = raw9[0]

    xbmc.log('*** eid      = %s' % eid)
    xbmc.log('*** pid      = %s' % pid)
    xbmc.log('*** sid      = %s' % sid)
    xbmc.log('*** epwatch  = %s' % epwatch)
    xbmc.log('*** sewatch  = %s' % sewatch)
    xbmc.log('*** h1       = %s' % h1)
    xbmc.log('*** Hash     = %s' % Hash)
    xbmc.log('*** Metadata = %s' % Metadata)
    xbmc.log('*** Plot     = %s' % Plot)

    meta_xml_bytes = meta_decoder(Metadata)
    xbmc.log('*** Metadata     = %s' % meta_xml_bytes)
    meta_root = ET.fromstring(meta_xml_bytes.encode('utf16'))   # See http://stackoverflow.com/questions/24045892

    def xpath_text_or_default(root, xpath, default):
        elements = root.findall(xpath)
        return elements[0].text if elements else default

    sources2_default = xpath_text_or_default(meta_root, './sources2/default', '')
    sources2_hq = xpath_text_or_default(meta_root, './sources2/hq', '')
    aspect = xpath_text_or_default(meta_root, './aspect', '0')
    duration = xpath_text_or_default(meta_root, './duration', '0')
    hq = int(xpath_text_or_default(meta_root, './hq', '0'))
    Eid = xpath_text_or_default(meta_root, './eid', '0')
    screen = xpath_text_or_default(meta_root, './screen', '')
    sizes_default = xpath_text_or_default(meta_root, './sizes/default', '0')
    sizes_hq = xpath_text_or_default(meta_root, './sizes/hq', '0')
    langs_en = xpath_text_or_default(meta_root, './langs/en', '0')
    langs_ru = xpath_text_or_default(meta_root, './langs/ru', '0')
    subtitles_en = xpath_text_or_default(meta_root, './subtitles/en', '0')
    subtitles_ru = xpath_text_or_default(meta_root, './subtitles/ru', '0')
    subtitles_en_sources = xpath_text_or_default(meta_root, './subtitles/sources/en', '')
    subtitles_ru_sources = xpath_text_or_default(meta_root, './subtitles/sources/ru', '')

    xbmc.log('    sources2_default = %s' % sources2_default)
    xbmc.log('         sources2_hq = %s' % sources2_hq)
    xbmc.log('              aspect = %s' % aspect)
    xbmc.log('            duration = %s' % duration)
    xbmc.log('                  hq = %s' % hq)
    xbmc.log('                 Eid = %s' % Eid)
    xbmc.log('              screen = %s' % screen)
    xbmc.log('       sizes_default = %s' % sizes_default)
    xbmc.log('            sizes_hq = %s' % sizes_hq)
    xbmc.log('            langs_en = %s' % langs_en)
    xbmc.log('            langs_ru = %s' % langs_ru)
    xbmc.log('        subtitles_en = %s' % subtitles_en)
    xbmc.log('        subtitles_ru = %s' % subtitles_ru)
    xbmc.log('subtitles_en_sources = %s' % subtitles_en_sources)
    xbmc.log('subtitles_ru_sources = %s' % subtitles_ru_sources)


    Hash = Hash[::-1]

    Lang = VIDEO_LANG
    Time = '0'
    #p0 = 'http://cdn.turbik.tv'
    #p0 = 'http://217.199.218.60'

    p1 = hashlib.sha1(Lang).hexdigest()
    p2 = str(eid)
    p3 = str(sources2_hq) if VIDEO_QUALITY == 'hq' and hq else str(sources2_default)
    p4 = str(Time)
    p5 = Hash
    p6 = hashlib.sha1(Hash + str(random.random())).hexdigest()
    p7 = hashlib.sha1(p6 + eid + 'A2DC51DE0F8BC1E9').hexdigest()
    retval = '/%s/%s/%s/%s/%s/%s/%s' % (p1, p2, p3, p4, p5, p6, p7)


    xbmc.log ('SRC file retval = %s' % retval)
    rurl = url.replace('/', '_')
    #dest = os.path.join(xbmc.translatePath('special://temp/'), rurl)
    #xbmc.log ('Dest file = %s' % dest)

    phpsessid = ''
    #req = urllib2.Request(durl)
    if os.path.isfile(phpsessid_file):
        fh = open(phpsessid_file, 'r')
        phpsessid = fh.read()
        fh.close()

    def play_url(path):
        conn = httplib.HTTPSConnection('cdn.turbik.tv', 443, timeout=10)

        headers = {
            'User-Agent':      'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.54 Safari/535.2',
            'Host':            'cdn.turbik.tv',
            'Accept':          '*/*',
            'Accept-Language': 'ru,en;q=0.9',
            'Accept-Charset':  'iso-8859-1, utf-8, utf-16, *;q=0.1',
            'Accept-Encoding': 'deflate, gzip, x-gzip, identity, *;q=0',
            'Referer':         'http://turbik.tv/media/swf/Player20.swf',
            'Cookie':          'IAS_ID='+str(phpsessid)+'; _',
            'Cookie2':         '$Version=1',
            'Connection':      'Keep-Alive'}

        conn.request("GET", path, '', headers)
        response = conn.getresponse()
        conn.close()
        xbmc.log ('Url: ' + str(path))
        xbmc.log ('Headers: ' + str(headers))
        xbmc.log ('Ret Status: ' + str(response.status))
        xbmc.log ('Ret Response: ' + str(response))
        if response.status == 302:
            xbmc.log('OK - response.status == 302')
            Location = response.getheader('Location')  # + '@'
            xbmc.log('Location: %s' % Location)

            #item = xbmcgui.ListItem(title, iconImage = thumb, thumbnailImage = thumb)
            #item.setInfo(type="Video", infoLabels = {
            #	"Title":	title,
            #	"Plot":		Plot
            #	} )

            h_1 = '|Referer=' + urllib.quote_plus('http://turbik.tv/media/swf/Player20.swf')
            h_2 = '&User-Agent=' + urllib.quote_plus('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.54 Safari/535.2')
            h_3 = '&Accept=' + urllib.quote_plus('*/*')
            h_4 = '&Accept-Language=' + urllib.quote_plus('ru,en;q=0.9')
            h_5 = '&Accept-Charset=' + urllib.quote_plus('iso-8859-1, utf-8, utf-16, *;q=0.1')
            h_6 = '&Accept-Encoding=' + urllib.quote_plus('deflate, gzip, x-gzip, identity, *;q=0')
            h_7 = '&Connection=' + urllib.quote_plus('Keep-Alive')
            #
            finalUrl = Location + h_1 + h_2 + h_3 + h_4 + h_5 + h_6 + h_7
            item = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb, path=finalUrl)
            item.setInfo(type="Video", infoLabels={
                "Title":	title,
                "Plot":		Plot
                })
            item.setProperty("IsPlayable", "true")
            item.setProperty('mimetype', 'video/mp4')

            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

            xbmc.Player().play(finalUrl, item)
            #xbmc.Player().play(finalItem)

            return
        return

    play_url(retval)


if run_once():
    params = get_params()
    mode = None
    url = ''
    title = ''
    ref = ''
    img = ''

    try:
        mode = urllib.unquote_plus(params["mode"])
    except:
        pass

    try:
        url = urllib.unquote_plus(params["url"])
    except:
        pass

    try:
        title = urllib.unquote_plus(params["title"])
    except:
        pass
    try:
        img = urllib.unquote_plus(params["img"])
    except:
        pass

    if mode == None:
        show_series('/Series/')
        xbmcplugin.setPluginCategory(handle, PLUGIN_NAME)
        xbmcplugin.endOfDirectory(handle)

    elif mode == 'OpenSeries':
        open_series(url, title)
        xbmcplugin.setPluginCategory(handle, PLUGIN_NAME)
        xbmcplugin.endOfDirectory(handle)

    elif mode == 'Watch':
        watch_episode(url, title, img)
        #xbmcplugin.setPluginCategory(handle, PLUGIN_NAME)
        #xbmcplugin.endOfDirectory(handle)