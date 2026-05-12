// 成語資料庫
const idiomsDatabase = [
    // 常用成語
    { idiom: '一石二鳥', meaning: '做一件事達到兩個目的', pinyin: 'yī shí èr niǎo', example: '這個計劃可以一石二鳥，既解決了問題又節省了成本。' },
    { idiom: '一箭雙鵰', meaning: '做一件事達到兩個目的', pinyin: 'yī jiàn shuāng diāo', example: '他的策略一箭雙鵰，既提高了效率又降低了成本。' },
    { idiom: '一鳴驚人', meaning: '平時默默無聞，一旦表現就令人驚嘆', pinyin: 'yī míng jīng rén', example: '他在比賽中一鳴驚人，打破了記錄。' },
    { idiom: '一舉兩得', meaning: '做一件事得到兩種好處', pinyin: 'yī jǔ liǎng dé', example: '學習英語可以一舉兩得，既能溝通又能了解文化。' },
    { idiom: '一帆風順', meaning: '做事順利，沒有阻礙', pinyin: 'yī fān fēng shùn', example: '祝你的新事業一帆風順。' },
    
    { idiom: '三心二意', meaning: '心思不專一，猶豫不決', pinyin: 'sān xīn èr yì', example: '做事不能三心二意，要專心致志。' },
    { idiom: '三思而行', meaning: '做事前要仔細考慮', pinyin: 'sān sī ér xíng', example: '這個決定很重要，一定要三思而行。' },
    { idiom: '三言兩語', meaning: '簡短的幾句話', pinyin: 'sān yán liǎng yǔ', example: '他三言兩語就說清楚了問題。' },
    
    { idiom: '不三不四', meaning: '不正派，不正經', pinyin: 'bù sān bù sì', example: '不要和那些不三不四的人來往。' },
    { idiom: '不恥下問', meaning: '不以向比自己差的人請教為恥', pinyin: 'bù chǐ xià wèn', example: '學習要不恥下問，才能進步。' },
    { idiom: '不約而同', meaning: '沒有約定而行動一致', pinyin: 'bù yuē ér tóng', example: '大家不約而同地鼓起掌來。' },
    
    { idiom: '五光十色', meaning: '色彩豐富，多種多樣', pinyin: 'wǔ guāng shí sè', example: '商場裡五光十色的商品令人眼花繚亂。' },
    { idiom: '五顏六色', meaning: '色彩豐富，多種多樣', pinyin: 'wǔ yán liù sè', example: '花園裡開滿了五顏六色的花。' },
    
    { idiom: '七上八下', meaning: '心神不安，忐忑不安', pinyin: 'qī shàng bā xià', example: '等待結果時，他的心情七上八下。' },
    { idiom: '七手八腳', meaning: '許多人一起動手', pinyin: 'qī shǒu bā jiǎo', example: '大家七手八腳地把東西搬上車。' },
    
    { idiom: '九牛一毛', meaning: '極其微小，微不足道', pinyin: 'jiǔ niú yī máo', example: '這點損失對他來說只是九牛一毛。' },
    
    { idiom: '十全十美', meaning: '完美無缺', pinyin: 'shí quán shí měi', example: '沒有什麼事情是十全十美的。' },
    
    // 動物相關
    { idiom: '畫蛇添足', meaning: '做多餘的事，反而弄巧成拙', pinyin: 'huà shé tiān zú', example: '這個修改是畫蛇添足，沒有必要。' },
    { idiom: '守株待兔', meaning: '不主動努力，希望僥倖獲得成功', pinyin: 'shǒu zhū dài tù', example: '不能守株待兔，要主動尋找機會。' },
    { idiom: '亡羊補牢', meaning: '出了問題後及時補救', pinyin: 'wáng yáng bǔ láo', example: '雖然已經出錯，但亡羊補牢為時不晚。' },
    { idiom: '馬到成功', meaning: '很快就成功', pinyin: 'mǎ dào chéng gōng', example: '祝你的新項目馬到成功。' },
    { idiom: '虎頭蛇尾', meaning: '開始認真，後來鬆懈', pinyin: 'hǔ tóu shé wěi', example: '這個項目虎頭蛇尾，最終失敗了。' },
    
    // 數字相關
    { idiom: '一心一意', meaning: '專心致志，沒有其他念頭', pinyin: 'yī xīn yī yì', example: '他一心一意地工作。' },
    { idiom: '兩全其美', meaning: '雙方都能得到好處', pinyin: 'liǎng quán qí měi', example: '這個方案可以兩全其美。' },
    { idiom: '三顧茅廬', meaning: '誠心誠意地邀請', pinyin: 'sān gù máo lú', example: '老闆三顧茅廬才請到他。' },
    { idiom: '四面楚歌', meaning: '陷入孤立無援的境地', pinyin: 'sì miàn chǔ gē', example: '他現在四面楚歌，沒有人支持他。' },
    { idiom: '五體投地', meaning: '非常佩服', pinyin: 'wǔ tǐ tóu dì', example: '我對他的能力五體投地。' },
    
    // 自然相關
    { idiom: '風和日麗', meaning: '天氣晴朗，微風和煦', pinyin: 'fēng hé rì lì', example: '今天是個風和日麗的好天氣。' },
    { idiom: '雨過天晴', meaning: '困難過去，情況好轉', pinyin: 'yǔ guò tiān qíng', example: '經過努力，終於雨過天晴。' },
    { idiom: '雪中送炭', meaning: '在困難時給予幫助', pinyin: 'xuě zhōng sòng tàn', example: '你的幫助真是雪中送炭。' },
    { idiom: '火中取栗', meaning: '冒險為他人做事，自己卻得不到好處', pinyin: 'huǒ zhōng qǔ lì', example: '他不想為別人火中取栗。' },
    
    // 更多常用成語
    { idiom: '畫龍點睛', meaning: '在關鍵處加上重要的內容，使作品更加出色', pinyin: 'huà lóng diǎn jīng', example: '這句話是整篇文章的畫龍點睛之筆。' },
    { idiom: '胸有成竹', meaning: '做事前已有完整的計劃', pinyin: 'xiōng yǒu chéng zhú', example: '他對這個計劃胸有成竹。' },
    { idiom: '井底之蛙', meaning: '見識短淺的人', pinyin: 'jǐng dǐ zhī wā', example: '不要做井底之蛙，要多看看外面的世界。' },
    { idiom: '朝三暮四', meaning: '反覆無常，沒有定見', pinyin: 'zhāo sān mù sì', example: '他朝三暮四，經常改變主意。' },
    { idiom: '對牛彈琴', meaning: '對不懂的人講深奧的道理', pinyin: 'duì niú tán qín', example: '跟他解釋這些概念，簡直是對牛彈琴。' },
    
    // 可以繼續添加更多成語...
];

// 成語管理類
class IdiomManager {
    constructor() {
        this.idioms = [...idiomsDatabase];
        this.usedIds = new Set();
    }

    // 獲取隨機成語
    getRandomIdiom() {
        if (this.usedIds.size >= this.idioms.length) {
            this.usedIds.clear(); // 重置已使用的成語
        }

        let availableIds = this.idioms
            .map((_, index) => index)
            .filter(id => !this.usedIds.has(id));

        if (availableIds.length === 0) {
            this.usedIds.clear();
            availableIds = this.idioms.map((_, index) => index);
        }

        const randomIndex = availableIds[Math.floor(Math.random() * availableIds.length)];
        this.usedIds.add(randomIndex);
        
        return this.idioms[randomIndex];
    }

    // 獲取所有成語
    getAllIdioms() {
        return this.idioms;
    }

    // 根據成語查找
    findIdiom(idiom) {
        return this.idioms.find(item => item.idiom === idiom);
    }

    // 獲取可接龍的成語（根據最後一個字）
    getChainIdioms(lastChar) {
        return this.idioms.filter(item => item.idiom[0] === lastChar);
    }

    // 生成填空題（隨機隱藏1-2個字）
    generateFillBlank(idiom) {
        const chars = idiom.split('');
        const blanks = Math.min(2, Math.floor(chars.length / 2)); // 最多隱藏2個字
        const blankIndices = [];
        
        while (blankIndices.length < blanks) {
            const index = Math.floor(Math.random() * chars.length);
            if (!blankIndices.includes(index)) {
                blankIndices.push(index);
            }
        }

        const display = chars.map((char, index) => {
            if (blankIndices.includes(index)) {
                return '_';
            }
            return char;
        });

        return {
            display: display.join(''),
            answers: blankIndices.map(i => chars[i]),
            blankIndices: blankIndices
        };
    }

    // 生成錯誤選項（用於選擇題）
    generateWrongOptions(correctMeaning, count = 3) {
        const wrongOptions = [];
        const availableMeanings = this.idioms
            .map(item => item.meaning)
            .filter(meaning => meaning !== correctMeaning);

        for (let i = 0; i < count; i++) {
            const randomIndex = Math.floor(Math.random() * availableMeanings.length);
            wrongOptions.push(availableMeanings[randomIndex]);
            availableMeanings.splice(randomIndex, 1);
        }

        return wrongOptions;
    }
}

// 導出（如果在 Node.js 環境）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { idiomsDatabase, IdiomManager };
}

