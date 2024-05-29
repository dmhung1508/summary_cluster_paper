import re

rmlist = ['ANTD.VN', 'Dân trí', 'VTC Now', 'VTC1','VTV24', 'VTV.vn', 'Vietnam+',  'VietnamPlus', 'TV24h', 'GĐXH', 'Tạp chí Doanh nghiệp Việt Nam', 'Kênh Ăn Ngủ Bóng Đá cập nhật liên tục', 'UNDP', 'VNEWS', 'PLO', 'Vnexpress', 'Theo: Vnexpress', 'blvquangtung', 'QuanTheThao',
          'ANTV', 'THVN', 'TV4K','quot','Bongda24h', 'Thethaovanhoa.vn', 'âm nhạc', 'Dân trí', 'ANTV','VTC News', 'SCMP', 'tintuc', 'THVN']

special_character = ["▶","🅙","🅑", "🅞", "✅","◉","()","|","[]","#"]
rmre = '|'.join(rmlist)



def clean_text(text, vocab=None):
    #clean HTML format
    cleanr = re.compile(r'<[^>]+>|<.*?>|&nbsp;|&amp;|&lt|p&gt|\u260e|<STYLE>(.*?)<\/STYLE>|<style>(.*?)<\/style>|\u2026')

    #delete text start with #
    pattern = re.compile(r'#\S+\s')
    text = pattern.sub('', text)

    #remove https
    text = re.sub(r'http\S+', '', text)
    text = re.sub(cleanr, ' ', text)

    #remove rmlist
    text = re.sub(re.compile(rmre), '', text)

    for char in special_character:
        if char in text:
            text = text.replace(char,'')
    text = text.replace("  "," ")
    return text