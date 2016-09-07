import feedparser, logging, re, time
from flask import Blueprint, render_template

mod = Blueprint('home', __name__, url_prefix='/<lang_code>', template_folder='../templates/home')

logger = logging.getLogger(__name__)

@mod.route('/')
def index():
    logger.info('Fetching blog posts...')

    blog_feed = feedparser.parse('http://blog.databasic.io/feed/')
    blog_posts = blog_feed['entries'][0:3]

    databasic_news = []
    for post in blog_posts:
        regex = re.match('(<img .*? />)?(.*?&#8230;)', post['description'])

        if regex.group(1) is not None:
            image = re.search('(?<=src=").*?(?=")', regex.group(1)).group(0)
        else:
            image = None

        logger.info('"%s" (%s)', post['title'], post['link'])

        databasic_news.append({
            'title': post['title'],
            'author': post['author'],
            'link': post['link'],
            'published': time.strftime('%B %d, %Y', post['published_parsed']),
            'description': regex.group(2),
            'image': image
        })

    return render_template('index.html', databasic_news=databasic_news)
