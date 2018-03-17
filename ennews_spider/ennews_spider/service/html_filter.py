# -*- coding:utf-8 -*-
import sys
from bs4 import BeautifulSoup

import re

try:
    from html.parser import HTMLParser
except:
    from HTMLParser import HTMLParser


class XssHtml(HTMLParser):
    allow_tags = ['img', 'br', 'strong', 'b', 'code', 'pre',
                  'p', 'em', 'span', 'h1', 'h2', 'h3', 'h4',
                  'h5', 'h6', 'blockquote', 'ul', 'ol', 'tr', 'th', 'td',
                  'hr', 'li', 'u', 's', 'caption', 'small', 'q', 'style', 'script']
    common_attrs = []
    nonend_tags = ["img", "hr", "br", "embed"]
    tags_own_attrs = {
        "img": ["src", "width", "height", "alt", "align"],
        "a": ["href", "rel", "title"],
        # "embed": ["src", "width", "height", "type", "allowfullscreen", "loop", "play", "wmode", "menu"],
        # "table": ["border", "cellpadding", "cellspacing"],
    }

    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style

    def __init__(self, allows=[]):
        HTMLParser.__init__(self)
        self.allow_tags = allows if allows else self.allow_tags
        self.result = []
        self.start = []
        self.data = []

    def getHtml(self):
        """
        Get the safe html code
        """
        for i in range(0, len(self.result)):
            tmp = self.result[i].rstrip('\n')
            tmp = tmp.lstrip('\n')
            if tmp:
                self.data.append(tmp)
        p = ''.join(self.data)

        result = self.re_script.sub('', p)  # 去掉SCRIPT
        result = self.re_style.sub('', result)  # 去掉SCRIPT
        return result

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if tag not in self.allow_tags:
            return
        end_diagonal = ' /' if tag in self.nonend_tags else ''
        if not end_diagonal:
            self.start.append(tag)
        attdict = {}
        for attr in attrs:
            attdict[attr[0]] = attr[1]

        attdict = self._wash_attr(attdict, tag)
        if hasattr(self, "node_%s" % tag):
            attdict = getattr(self, "node_%s" % tag)(attdict)
        else:
            attdict = self.node_default(attdict)

        attrs = []
        for (key, value) in attdict.items():
            attrs.append('%s="%s"' % (key, self._htmlspecialchars(value)))
        attrs = (' ' + ' '.join(attrs)) if attrs else ''
        self.result.append('<' + tag + attrs + end_diagonal + '>')

    def handle_endtag(self, tag):
        if self.start and tag == self.start[len(self.start) - 1]:
            self.result.append('</' + tag + '>')
            self.start.pop()

    def handle_data(self, data):
        self.result.append(self._htmlspecialchars(data))

    def handle_entityref(self, name):
        if name.isalpha():
            self.result.append("&%s;" % name)

    def handle_charref(self, name):
        if name.isdigit():
            self.result.append("&#%s;" % name)

    def node_default(self, attrs):
        attrs = self._common_attr(attrs)
        return attrs

    def node_a(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "href")
        attrs = self._set_attr_default(attrs, "target", "_blank")
        attrs = self._limit_attr(attrs, {
            "target": ["_blank", "_self"]
        })
        return attrs

    def node_embed(self, attrs):
        attrs = self._common_attr(attrs)
        attrs = self._get_link(attrs, "src")
        attrs = self._limit_attr(attrs, {
            "type": ["application/x-shockwave-flash"],
            "wmode": ["transparent", "window", "opaque"],
            "play": ["true", "false"],
            "loop": ["true", "false"],
            "menu": ["true", "false"],
            "allowfullscreen": ["true", "false"]
        })
        attrs["allowscriptaccess"] = "never"
        attrs["allownetworking"] = "none"
        return attrs

    def _true_url(self, url):
        prog = re.compile(r"^(http|https|ftp)://.+", re.I | re.S)
        if prog.match(url):
            return url
        else:
            return "http://%s" % url

    def _true_style(self, style):
        if style:
            style = re.sub(r"(\\|&#|/\*|\*/)", "_", style)
            style = re.sub(r"e.*x.*p.*r.*e.*s.*s.*i.*o.*n", "_", style)
        return style

    def _get_style(self, attrs):
        if "style" in attrs:
            attrs["style"] = self._true_style(attrs.get("style"))
        return attrs

    def _get_link(self, attrs, name):
        if name in attrs:
            attrs[name] = self._true_url(attrs[name])
        return attrs

    def _wash_attr(self, attrs, tag):
        if tag in self.tags_own_attrs:
            other = self.tags_own_attrs.get(tag)
        else:
            other = []
        if attrs:
            for (key, value) in attrs.items():
                if key not in self.common_attrs + other:
                    del attrs[key]
        return attrs

    def _common_attr(self, attrs):
        attrs = self._get_style(attrs)
        return attrs

    def _set_attr_default(self, attrs, name, default=''):
        if name not in attrs:
            attrs[name] = default
        return attrs

    def _limit_attr(self, attrs, limit={}):
        for (key, value) in limit.items():
            if key in attrs and attrs[key] not in value:
                del attrs[key]
        return attrs

    def _htmlspecialchars(self, html):
        return html.replace("<", "&lt;") \
            .replace(">", "&gt;") \
            .replace('"', "&quot;") \
            .replace("'", "&#039;")


if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html_str):
    s = MLStripper()
    s.feed(html_str)
    return s.get_data()


def extract(html_str, filter_list):
    soup = BeautifulSoup(html_str, 'lxml')

    for tag in soup.recursiveChildGenerator():
        if hasattr(tag, 'name') and tag.name in filter_list:
            tag.extract()
            print tag


if __name__ == '__main__':
    html = """
   <div class="text" id="text">
                        <p>　　消费者称收到&ldquo;枯叶残花&rdquo; 由明星高圆圆投资引关注</p>
<p>　　由影视明星高圆圆与他人合作投资的鲜花品牌&ldquo;花点时间&rdquo;，一推出就受到广大年轻女性追捧。但近期，不少消费者反映，自己收到的鲜花和网上展示图片存在较大差异，甚至还收到&ldquo;枯叶残花&rdquo;。也有消费者表示，售后只能通过在线客服，遇到问题不能及时解决。昨天，北京晨报记者体验发现，只能通过微信联系在线客服，且客服回复较慢，每次都要几分钟回答一个问题。</p>
<p>　　■网友声音</p>
<p>　　各种滋味sharing：好期待有一天女神能亲自送花!</p>
<p>　　土星回归之年：两周前订的母亲节送花，到现在都没收到花。</p>
<p>　　不记得小姐：你们家不光是花的质量差，客服还永远不在线。</p>
<p><strong>　　包月鲜花数量减半</strong></p>
<p>　　消费者杨女士告诉记者，4月底，她在花点时间团购了99元包月的自然系列鲜花，一次性支付三个月费用。据杨女士订单信息显示，该系列鲜花原价为139元每月，每周一束。&ldquo;参加这个活动需要邀请好友，我还拉了两个朋友参团。&rdquo;杨女士说，迄今为止两次收到的鲜花，她都不太满意。</p>
<p>　　&ldquo;第一次收到花时，我就傻眼了。&rdquo;杨女士说，好几支花都&ldquo;病怏怏&rdquo;的。据杨女士上传到微博的照片，记者看到其中一支芍药花瓣显得皱巴巴，另一支花上的绿叶&ldquo;蜷缩&rdquo;起来。杨女士告诉记者，&ldquo;第二次送的康乃馨还折断了，洋兰的花茎又太短，插不到瓶底，周一的好心情，全部被破坏了。&rdquo;</p><div class="ad250x250 fLeft marRig10" id="adPp"><!-- Ad Survey 广告位代码  文章内页画中画08--><script type="text/javascript">AD_SURVEY_Add_AdPos("9263");</script></div>
<p>　　无独有偶，另一位消费者朱女士向记者反映，5月初收到的花令其非常失望。&ldquo;效果图中有好几支女贞叶，结果就收到了一支，而且叶子已经枯黄。&rdquo;朱女士说，效果图上每种花都有好几支，但是到手之后，发现每种花的数量都少了近一半。
<p>　　在网上，记者发现近期吐槽花点时间的消费者不在少数，吐槽内容主要集中在&ldquo;花朵质量差&rdquo;、&ldquo;投诉没回复&rdquo;、&ldquo;找不到客服&rdquo;等。
<p><strong>　　客服电话很难拨通</strong>
<p>　　花点时间微信公众号信息显示，该店是影视明星高圆圆与他人合作投资的品质鲜花店，注册公司为花意生活(北京)电子商务有限公司。在其网页上，有&ldquo;都市女性悦己生活从每周一束精致鲜花开始&rdquo;的宣传语，店里展示着各种主题的产品，价格从99元至468元不等。
<p>　　记者看到微信公众号主页面，显示有一个010开头的&ldquo;客服电话&rdquo;，记者多次拨打该号码，刚&ldquo;嘟&rdquo;完一声就被自动挂断，记者连续尝试十几次，均是如此。
<p>　　随后，记者在微信公众号右下角找到了&ldquo;联系客服&rdquo;，有售前咨询和售后服务两项。记者点击售后服务后，需要手机短信验证码登录，由于记者此前没有下过单，无法进入在线客服。但据杨女士和朱女士反映，售后服务联系起来相当困难，每次要想和人工客服取得联系，需要漫长等待，&ldquo;有一次我反映情况，显示在线排队人数有100多人，你想想这售后服务体验能好到哪里去？&rdquo;
<p>　　记者又联系到&ldquo;售前咨询&rdquo;转人工服务，等待近三分钟后与人工取得联系，对方称，他们的产品都是本地就近发货，但对于消费者反映鲜花质量参差不齐的问题，对方没有做任何回应。
<p>　　北京晨报热线新闻 记者 汪慧贤 线索：辰先生
                        <!-- Ad Survey 广告位代码  文章页 视频广告-->
                        <script type="text/javascript">AD_SURVEY_Add_AdPos("14213");</script>

                                                <!--相关新闻上方合作 begain-->

                        <!--相关新闻上方合作 end-->
                        <!--相关新闻 begain-->
                                                                                                <!--相关新闻 end-->

                        <!--相关专题 begain-->
                        <div class="spTopic">
                                                    </div>
                        <!--相关专题 end-->
                        <!-- 责任编辑&版权 begin-->
                        <div class="editorSign" style="border-top: none;">
                            <span id="editor_baidu" style="border-left: none;">责编：李青云</span>
                        </div>
                        <!-- 责任编辑&版权 begin-->
                        <!--版权印 begin-->
                                                <!--版权印 end-->
                    </div>
    """

    # print strip_tags(html)
    # extract(html, ['p', 'strong', 'img'])
    parser = XssHtml()
    parser.feed(html)
    parser.close()
    print parser.getHtml()

