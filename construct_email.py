from paper import ArxivPaper
import math
from tqdm import tqdm
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import datetime
from loguru import logger

framework = """
<!DOCTYPE HTML>
<html>
<head>
  <style>
    .star-wrapper {
      font-size: 1.3em; /* 调整星星大小 */
      line-height: 1; /* 确保垂直对齐 */
      display: inline-flex;
      align-items: center; /* 保持对齐 */
    }
    .half-star {
      display: inline-block;
      width: 0.5em; /* 半颗星的宽度 */
      overflow: hidden;
      white-space: nowrap;
      vertical-align: middle;
    }
    .full-star {
      vertical-align: middle;
    }
  </style>
</head>
<body>

<div>
    __CONTENT__
</div>

<br><br>
<div>
__FOOTER__
</div>

</body>
</html>
"""

def is_chinese(language: str) -> bool:
  return language.lower().startswith('chinese') or language.lower().startswith('zh')

def get_footer(language: str) -> str:
  if is_chinese(language):
    return '如需停止接收，请删除 GitHub Actions Secret 中的收件邮箱配置。'
  return 'To unsubscribe, remove your email in your Github Action setting.'

def get_empty_html(language: str):
  block_template = """
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
  <tr>
    <td style="font-size: 20px; font-weight: bold; color: #333;">
        __EMPTY_TEXT__
    </td>
  </tr>
  </table>
  """
  empty_text = '今日暂无新论文，休息一下吧。' if is_chinese(language) else 'No Papers Today. Take a Rest!'
  return block_template.replace('__EMPTY_TEXT__', empty_text)

def get_block_html(title:str, authors:str, rate:str,arxiv_id:str, abstract:str, pdf_url:str, code_url:str=None, affiliations:str=None, language: str='English'):
    code = f'<a href="{code_url}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #5bc0de; padding: 8px 16px; border-radius: 4px; margin-left: 8px;">Code</a>' if code_url else ''
    relevance_label = '相关度' if is_chinese(language) else 'Relevance'
    arxiv_label = 'arXiv 编号' if is_chinese(language) else 'arXiv ID'
    tldr_label = '摘要推荐' if is_chinese(language) else 'TLDR'
    code_label = '代码' if is_chinese(language) else 'Code'
    code = code.replace('>Code<', f'>{code_label}<')
    block_template = """
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
    <tr>
        <td style="font-size: 20px; font-weight: bold; color: #333;">
            {title}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #666; padding: 8px 0;">
            {authors}
            <br>
            <i>{affiliations}</i>
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>{relevance_label}:</strong> {rate}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>{arxiv_label}:</strong> <a href="https://arxiv.org/abs/{arxiv_id}" target="_blank">{arxiv_id}</a>
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>{tldr_label}:</strong> {abstract}
        </td>
    </tr>

    <tr>
        <td style="padding: 8px 0;">
            <a href="{pdf_url}" style="display: inline-block; text-decoration: none; font-size: 14px; font-weight: bold; color: #fff; background-color: #d9534f; padding: 8px 16px; border-radius: 4px;">PDF</a>
            {code}
        </td>
    </tr>
</table>
"""
    return block_template.format(
        title=title,
        authors=authors,
        rate=rate,
        arxiv_id=arxiv_id,
        abstract=abstract,
        pdf_url=pdf_url,
        code=code,
        affiliations=affiliations,
        relevance_label=relevance_label,
        arxiv_label=arxiv_label,
        tldr_label=tldr_label,
    )

def get_stars(score:float):
    full_star = '<span class="full-star">⭐</span>'
    half_star = '<span class="half-star">⭐</span>'
    low = 6
    high = 8
    if score <= low:
        return ''
    elif score >= high:
        return full_star * 5
    else:
        interval = (high-low) / 10
        star_num = math.ceil((score-low) / interval)
        full_star_num = int(star_num/2)
        half_star_num = star_num - full_star_num * 2
        return '<div class="star-wrapper">'+full_star * full_star_num + half_star * half_star_num + '</div>'


def render_email(papers:list[ArxivPaper], language: str='English'):
    parts = []
    if len(papers) == 0 :
        return framework.replace('__CONTENT__', get_empty_html(language)).replace('__FOOTER__', get_footer(language))
    
    for p in tqdm(papers,desc='Rendering Email'):
        rate = get_stars(p.score)
        author_list = [a.name for a in p.authors]
        num_authors = len(author_list)
        
        if num_authors <= 5:
            authors = ', '.join(author_list)
        else:
            authors = ', '.join(author_list[:3] + ['...'] + author_list[-2:])
        if p.affiliations is not None:
            affiliations = p.affiliations[:5]
            affiliations = ', '.join(affiliations)
            if len(p.affiliations) > 5:
                affiliations += ', ...'
        else:
            affiliations = '未知机构' if is_chinese(language) else 'Unknown Affiliation'
        parts.append(get_block_html(p.title, authors,rate,p.arxiv_id ,p.tldr, p.pdf_url, p.code_url, affiliations, language=language))

    content = '<br>' + '</br><br>'.join(parts) + '</br>'
    return framework.replace('__CONTENT__', content).replace('__FOOTER__', get_footer(language))

def send_email(sender:str, receiver:str, password:str,smtp_server:str,smtp_port:int, html:str, language: str='English'):
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    msg = MIMEText(html, 'html', 'utf-8')
    sender_name = '每日 Zotero 论文推荐' if is_chinese(language) else 'Github Action'
    receiver_name = '你' if is_chinese(language) else 'You'
    msg['From'] = _format_addr(f'{sender_name} <{sender}>')
    msg['To'] = _format_addr(f'{receiver_name} <{receiver}>')
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    subject = f'每日 arXiv 推荐 {today}' if is_chinese(language) else f'Daily arXiv {today}'
    msg['Subject'] = Header(subject, 'utf-8').encode()

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
    except Exception as e:
        logger.warning(f"Failed to use TLS. {e}")
        logger.warning(f"Try to use SSL.")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)

    server.login(sender, password)
    server.sendmail(sender, [receiver], msg.as_string())
    server.quit()
