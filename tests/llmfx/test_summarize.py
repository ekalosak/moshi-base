import pytest

from moshi import Message, Role
from moshi.llmfx import summarize

TEXT = """
Frederick Douglass (born Frederick Augustus Washington Bailey, c. February 1817 or 1818[a] – February 20, 1895) was an American social reformer, abolitionist, orator, writer, and statesman. After escaping from slavery in Maryland, he became a national leader of the abolitionist movement in Massachusetts and New York, during which he gained fame for his oratory[4] and incisive antislavery writings. Accordingly, he was described by abolitionists in his time as a living counterexample to enslavers' arguments that enslaved people lacked the intellectual capacity to function as independent American citizens.[5] Northerners at the time found it hard to believe that such a great orator had once been enslaved. It was in response to this disbelief that Douglass wrote his first autobiography.[6]

Douglass wrote three autobiographies, describing his experiences as an enslaved person in his Narrative of the Life of Frederick Douglass, an American Slave (1845), which became a bestseller and was influential in promoting the cause of abolition, as was his second book, My Bondage and My Freedom (1855). Following the Civil War, Douglass was an active campaigner for the rights of freed slaves and wrote his last autobiography, Life and Times of Frederick Douglass. First published in 1881 and revised in 1892, three years before his death, the book covers his life up to those dates. Douglass also actively supported women's suffrage, and he held several public offices. Without his knowledge or consent, Douglass became the first African American nominated for vice president of the United States, as the running mate of Victoria Woodhull on the Equal Rights Party ticket.[7]

Douglass believed in dialogue and in making alliances across racial and ideological divides, as well as in the liberal values of the U.S. Constitution.[8] When radical abolitionists, under the motto "No Union with Slaveholders", criticized Douglass's willingness to engage in dialogue with slave owners, he replied: "I would unite with anybody to do right and with nobody to do wrong."[9] 
"""

TEXT2 = """
《大英百科全書》（又称《不列顛百科全書》；拉丁語：Encyclopædia Britannica），是由私人大英百科全書出版社所出版的英語百科全書，被认为是当今世界上最具权威的百科全书，是英語世界俗稱的ABC百科全書之一。大英百科全書的條目由大約100名全職編輯及超過4000名專家編寫而成。它被普遍認為是最有學術性的百科全書。[1][2]

《大英百科全書》是現存仍然發行的最古老的英語百科全書。[3]它於1768年至1771年間在英國爱丁堡首次問世，立刻受到讀者歡迎，且出版規模日漸擴大。平均13年左右出一次新版[4]（p. 145）。1801年的第三版冊數已達21。[5][6]隨著其地位的日益提高，作者團隊招賢納士也變得更加容易。1875年至1889年間的第9版和1911年的第11版被認為是學術與文學風格兼并的標誌性百科全書。[5]從第11版起，《大英百科全書》的條目趨於精簡，以進軍北美市場。[5]1933年，《大英百科全書》采取「連續性修訂」政策，即不斷再版並定期更新條目。[6]經過70多年的時間洗禮，《大英百科全書》的數量規模已保持穩定，字數維持在4千萬上下，涵蓋約50萬個主題。[7]20世纪80年代起，大英百科全書出版社與中国大百科全书出版社合作出版了《大英百科全書》的簡體中文版[8]。1994年正式發行的《大英線上百科全書》（Encyclopedia Britannica Online）除包括實體書内容外，还包括最新修訂和大量實體書中没有的文章，可檢索詞條達到98,000個，收錄了322幅手繪線條圖、9,811張照片、193幅國旗、337幅地圖、204段影片、714張表格等豐富内容。雖然在1901年它的出版地變更為美國，《大英百科全書》依然保留了英式英語的拼寫規則。[1] 
"""

CORPORA = {
    "en-US": TEXT,
    "zh-CN": TEXT2,
}

@pytest.mark.parametrize('bcp47', ["en-US", "zh-CN"])
@pytest.mark.openai
def test_summarize(bcp47: str):
    text = CORPORA[bcp47]
    msgs = [Message(Role.USR, t) for t in text.split("\n") if t]
    summary = summarize.summarize(msgs, 5, bcp47)
    print(f"Summary: {summary}")
    assert len(summary) < 50, "Summary response too long."