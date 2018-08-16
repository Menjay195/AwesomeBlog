在blogs.html中，
<p class="uk-article-meta">发表于{{ blog.created_at }}</p>
显示出的时间是浮点数。
修改为<p class="uk-article-meta">发表于{{ blog.created_at|datetime }}</p>
才会通过jinja2的filter渲染，即app.py定义的datetime_filter处理后渲染显示。


测试程序：
python3 app.py
