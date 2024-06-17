// ==UserScript==
// @name         北化在线测试Dumper
// @namespace    http://tampermonkey.net
// @version      2024-05-27
// @description  Dumper for ChemE Course 化工原理!
// @author       Snowman
// @match        https://course.buct.edu.cn/meol/common/question/test/student/stu_qtest_result.jsp*
// @icon         https://www.google.com/s2/favicons?domain=buct.edu.cn
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// ==/UserScript==


class DumpCore {

    static dumpCurrent() {
        const tbodys = document.querySelectorAll('tbody');

        // 测试总体情况
        const t_summary = tbodys[0];
        // 显示错题情况
        const t_validated = tbodys[1];
        // 所有的题目
        const t_questions = [...tbodys].slice(2)

        const temp = [...t_summary.querySelectorAll('td')].map(i => i.firstChild)
        const summary = {
            'max_score': parseFloat(temp[0].innerText),
            'score': parseFloat(temp[1].innerText),
            'max_rank': parseInt(temp[2].innerText),
            'rank': parseInt(temp[3].textContent),
        }
        const validated = t_validated.classList.contains('switch-on');
        const content = DumpCore._parseQuestions(t_questions);
        const {testId, answerId} = DumpCore._parseContext();

        const result = {
            'summary': summary,
            'validated': validated,
            'content': content,
            'testId': testId,
            'answerId': answerId,
        };

        console.log(`成功Dump了当前内容（状态：${validated ? '正' : '未'}显示错题）`, result);
        // DumpCore.saveResult(result);
        return result;
    }

    static _parseQuestions(t_questions) {

        const result = {};
        let cnt = 0;

        function cutPrefix(text, prefix) {
            if (text.startsWith(prefix))
                return text.substring(prefix.length)
            else
                return text
        }

        function getHash(text) {
            let hash = 0;
            if (text.length === 0) {
                throw new Error('不得对空字符串哈气！');
            }
            for (let i = 0; i < text.length; i++) {
                let char = text.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return hash;
        }

        for (const tbody of t_questions) {

            // tbodytr[0]
            const texts = [...tbody.querySelectorAll('.E')].map(i => i.innerText);
            const number = parseInt(cutPrefix(texts[0], '试题'));
            const max_score = parseFloat(texts[1].match(/满分值：([\d.]+)/)[1]);

            // tbodytr[2]
            const my_answer = cutPrefix(tbody.querySelector('.F').innerText, '[我的答案] ');

            // tbodytr[1]
            const question_html = tbody.querySelector('input[type=hidden]').value;
            const t_choices = [...tbody.querySelectorAll('input.none')];

            let type, choices, answer;

            if (t_choices.length === 0) {

                type = 3; // '判断'
                choices = ['错误', '正确'];
                answer = choices.findIndex(i => i === my_answer);

                if (answer === -1) type = -1;

            } else {

                if (t_choices[0].type === 'radio') type = 1; // '单选'
                else if (t_choices[0].type === 'checkbox') type = 2; // '多选'
                else type = -1;

                choices = t_choices.map(i => i.nextSibling.textContent.trimEnd());

                answer = [];
                for (let i = 0; i < t_choices.length; i++)
                    if (t_choices[i].checked) answer.push(i);
                if (answer.length === 1) answer = answer[0];

            }

            //const hash = getHash(question_html);

            //if(result[hash] !== undefined) {
            //    console.warn('[SnowDump] 卧槽！哈希碰撞！');
            //    alert('[SnowDump] 严重错误！');
            //}

            result[cnt++] = {
                'desc': question_html,
                'type': type,
                // 'number': number,
                // 'max_score': max_score,
                'choices': choices,
                'answer_idx': answer,
            };
        }

        return result;
    }

    static _parseContext() {
        let params = new URLSearchParams(window.location.search);
        return {
            'testId': params.get('testId'),
            'answerId': params.get('answerId'),
        }
    }

    static async saveResult(result) {
        let old = await GM.getValue(result.testId);
        if (old === undefined) {
            GM.setValue(result.testId, result);
            console.log(`[SnowDump] 已保存结果 (testId = ${result.testId})`);
            return;
        }
        if (result.validated === old.validated) {
            if (result.score > old.score) {
                GM.setValue(result.testId, result);
                console.log(`[SnowDump] 已覆盖分数更低的旧结果 (testId = ${result.testId})`);
            } else {
                console.log(`[SnowDump] 未保存分数更低的新结果 (testId = ${result.testId})`);
            }
            return;
        }

        console.log(GM);
    }
}


// ----------------------- init -----------------------

GM.registerMenuCommand('Dump - 导出题目', DumpCore.dumpCurrent);

window.dumpCore = DumpCore;
window.dumpNow = DumpCore.dumpCurrent;
console.log("[SnowDump] 调用 dumpNow() 以进行导出");

// ---------------------- init -----------------------


