def generate_url(request, url_path=None):
    return f'{request.scheme}://{request.get_host()}/{url_path}'
