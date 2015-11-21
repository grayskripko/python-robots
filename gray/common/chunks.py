def chunk():
    url = "http://url.com"
    import webbrowser
    webbrowser.open(url)

    import requests
    import bs4
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text)
    return [a.attrs.get('href') for a in soup.select('#video-summary-content strong a[href*=/video/]')]
