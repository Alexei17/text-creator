# -*- coding: utf-8 -*-
import random
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pymorphy2
from nltk.tokenize.treebank import TreebankWordDetokenizer
# CONSTANT DECLARATION SECTION
manual_entry = False #при False будет давать опцию пользователю вводить параметры
stopwords = set(stopwords.words('russian')) #стоп слова на русском
morph = pymorphy2.MorphAnalyzer()
tryReplaceTimes = 100 #попытки преобразования слова
# CONSTANT DECLARATION SECTION END


# INPUT SECTION
if manual_entry:
    randomCoefficient = 0.5 #шанс замены какого-либо слова из оригинала
    # needToReplace = True #при true будет заменять из заданного файла, при false из русского словаря - пока что не поддерживается
    debugMode = True

else:
    inp = int(input("Заменить примерно каждое ___ слово "))
    randomCoefficient = 1/inp
    inp = int(input('Debug mode? (0/1)'))
    if inp == 1:
        debugMode = True
    else:
        debugMode = False
# INPUT SECTION END


# PRE LOADING SECTION
with open('file.txt') as f:
    original = f.read().split('\n')


# if needToReplace:
with open('filetoreplacewith.txt') as f:
    replacement_raw = f.read()
    replacement = replacement_raw.split('\n')
    replacement_tokens = word_tokenize(replacement_raw)


    
# PRE LOADING SECTION END
def isALegalWord(w): #небольшой метод для проверки того, является ли текст вообще словом и если да, то нету ли его в стоп словах. Предотвращает чтобы '.' и тому подобные считались за слово.
    if not (w.lower() in stopwords) and w.isalpha():
        return True
    else:
        return False

def debugLog(text): #небольшой декоратор, если дебаг режим включен распечатает
    if debugMode:
        print(text)



def analyzeNumber(original, toRep): #возращает слово если успешно, False если не получилось
    if ('Sgtm' in toRep.tag or 'Pltm' in toRep.tag): 
    #Если Sgtm или Pltm присутствует, то данное слово может употребляться только в ед. и мн. числе соотвественно. Менять число не нужно.
        return original
    try:
        toRep = toRep.inflect({original.tag.number}) #меняем в форму оригинального слова
        return toRep

    except AttributeError: #слово преобразовать не получилось
        return False

def analyzeCase(original, toRep): #возращает слово если успешно, False если не получилось
    try:
        toRep = toRep.inflect({original.tag.case}) #меняем в падеж оригинального слова
        return toRep

    except AttributeError: #слово преобразовать не получилось
        return False

def analyzeMood(original, toRep): #возращает слово если успешно, False если не получилось
    try:
        toRep = toRep.inflect({original.tag.mood}) #меняем в падеж оригинального слова
        return toRep

    except AttributeError: #слово преобразовать не получилось
        return False

def analyzeAspect(original, toRep):
    try:
        toRep = toRep.inflect({original.tag.aspect}) #меняем вид
        return toRep

    except AttributeError: #слово преобразовать не получилось
        return False

def analyzeTense(original, toRep):
    try:
        toRep = toRep.inflect({original.tag.tense}) #меняем вид
        return toRep

    except AttributeError: #слово преобразовать не получилось
        return False

def checkComboForGenderAndNumber(prevWord, newWord):
    #здесь мы делаем проверку на предыдущое слово. если предыдущее слово прилагательное/причастие/причастие а следующее существительное
    #, приэтом у существительного выражен род (м/ж/ср), то нужно сделать проверку на род прилагательного.
    # так, например, вместо 'неравномерный площадь' получится 'неравномерная площадь'
    # функция возращает те же prevword и newWord и boolean, True если изменилось слово предудыщое и False иначе
    # так же делает проверку на число. если сущесвтительное в множественном/единственном, то и прилагательное/причастие такое
    # пример проверки на число: 'технологического введений' -> 'технологических введений'
    didChange = False
    checkArray = ['PRTF', 'ADJF', 'NOUN'] #проверям на прилагательные или причастия, так же существительных
    prevWordOriginal = prevWord
    try:
        if (prevWord.tag.POS in checkArray and newWord.tag.POS == 'NOUN') and (not('GNdr' in newWord.tag)):
            debugLog(f'Преобразовываю прилагательное/причастие (род): {prevWord.word}')
            prevWord = prevWord.inflect({newWord.tag.gender})
            debugLog(f'Результат: {prevWord.word}')
            didChange = True

    except AttributeError:
        debugLog('не смог преобразовать род с прилагательным и существительным')
        pass

    finally: #преобразование числа
        try:
            if ((prevWord.tag.POS in checkArray and newWord.tag.POS == 'NOUN') or (prevWord.tag.POS == 'NOUN' and newWord.tag.POS in checkArray)) and (prevWord.tag.number != newWord.tag.number):
                debugLog(f'Преобразовываю прилагательное/причастие (число): {prevWord.word}')
                prevWord = prevWord.inflect({newWord.tag.number})
                debugLog(f'Результат: {prevWord.word}')
                didChange = True

        except AttributeError:
            debugLog('не смог преобразовать число с прилагательным и существительным')

    if (prevWord == None):
        prevWord = prevWordOriginal

    return prevWord, newWord, didChange
            
    

def checkPrepCase(prevWord, newWord):
    debugLog('предлог check')
    # функция проверки употребления существительного с предлогом. 
    # может превращать фразы по типу 'в числа' -> 'в числе'
    # возращает слово если успешно и False если возникла ошибка
    prepList = {
        "gent": ['от', 'без', 'у', 'до', 'возле', 'для', 'вокруг', 'из', 'около', 'с', 'из-за', 'из-под', 'вроде', 'среди', 'между', 'кроме'],
        "datv": ['по', 'к'],
        "accs": ['на', 'за', 'через', 'про', 'под', 'в'],
        "ablt": ['за', 'под', 'над', 'перед', 'с', 'между'],
        "loct": ['о', 'об', 'на', 'во', 'при', 'обо']
    } #взято отсюда https://izamorfix.ru/rus/morfologiya/padeji_suschestvit.html

    try:
        prepCase = [case for case, wordList in prepList.items() if prevWord.word in wordList][0] 
        #возвращает падеж предлога. для 'в' вернет ablt
    except IndexError: #предлог не найден
        return False
    
    try:
        newWord = newWord.inflect({prepCase})
    except AttributeError:
        return False

    return newWord

def tryToReplace(original, toRep): #возращает слово если успешно, False если не получилось
    original = morph.parse(original)[0]
    toRep = morph.parse(toRep)[0]

    if (original.tag.POS == 'ADVB'):
        return original #с наречиями не работаем, с ними куча каши получается, извините :P

    #разбор части речи, если они не совпадают то смысла рассматривать такое слово скорее всего нету
    if (original.tag.POS != toRep.tag.POS):
        debugLog(f'попробовал заменить на {toRep.word}: часть речи не совпадает')
        return False

    
    if (original.tag.POS == 'VERB'): #для глагола будет отдельный разбор
        # разбор наклонения
        if (original.tag.mood != None and (original.tag.mood != toRep.tag.mood)):
            moodAnalyzer = analyzeMood(original, toRep)
            if moodAnalyzer == False:
                debugLog(f'попробовал поменять наклонение со словом {toRep.word}: не получилось')
                return False
            toRep = moodAnalyzer
        
        if (original.tag.aspect != None and (original.tag.aspect != toRep.tag.aspect)):
            analyzeAspect = analyzeMood(original, toRep)
            if analyzeAspect == False:
                debugLog(f'попробовал поменять вид (совершенный/несовершенный) со словом {toRep.word}: не получилось')
                return False
            toRep = analyzeAspect
        
        if (original.tag.tense != None):
            tenseAn = analyzeTense(original, toRep)
            if tenseAn == False:
                debugLog(f'попробовал поменять время со словом {toRep.word}: не получилось')
                return False
            toRep = tenseAn
  
    #разбираем число, если не совпадают пробуем преобразовать
    if (original.tag.number != toRep.tag.number):
        numAnalyzer = analyzeNumber(original, toRep)
        if numAnalyzer == False:
            debugLog(f'попробовал поменять число со словом {toRep.word}: не получилось')
            return False
        toRep = numAnalyzer
        
    #разбор падежа
    if (original.tag.case != toRep.tag.case):
        caseAnalyzer = analyzeCase(original, toRep)
        if caseAnalyzer == False:
            debugLog(f'попробовал поменять падеж со словом {toRep.word}: не получилось')
            return False
        toRep = caseAnalyzer

    
    return toRep


def endCheck(prevWord, newWord):
    #метод для проверки связи предыдущего и текущего слова. возвращает старое, новое слово и bool который говорит, были ли изминения
    didChange = False
    if prevWord != None:
        prevWord, newWord, check = checkComboForGenderAndNumber(prevWord, newWord)
        if check == True:
            didChange = True
        
        if prevWord.tag.POS == 'PREP' and newWord.tag.POS == 'NOUN': #является ли предыдущее слово предлогом и данное существительным
            check = checkPrepCase(prevWord, newWord)
            if check != False:
                newWord = check
                didChange = True


    return prevWord, newWord, didChange

# PROGRAM MAIN
out = [] #вывод
for sentence in original:
    words = word_tokenize(sentence) #токенизируем
    prevWord = None
    for word in words:
        tries = 0
        if random.random() <= randomCoefficient: #будем заменять?
            if isALegalWord(word):
                while tries < tryReplaceTimes:
                    randomWord = replacement_tokens[random.randint(0, len(replacement_tokens)-1)]
                    newWord = tryToReplace(word, randomWord)
                    if newWord == False:
                        tries += 1
                        continue
                    else:
                        #закончили: подобрали слово. сделаем последние проверки
                        prevWord, newWord, didChange = endCheck(prevWord, newWord)
                        if didChange:
                            out[-1] = prevWord.word #меняем предыдущое слово в связи с проверкой

                        prevWord = newWord

                        break
                
                if tries >= tryReplaceTimes:
                    #не повезло не повезло, оставляем то же слово
                    debugLog(word)
                    out.append(word)
                else:
                    out.append(newWord.word)
                    debugLog(f'{word} + {randomWord} -> {newWord.word}')
            
            else:
                newWord = morph.parse(word)[0] #стоп-слово или не является словом, оставим как есть
                prevWordT, newWordT, didChange = endCheck(prevWord, newWord)
                if didChange:
                    if prevWordT != prevWord: #чтобы не менять лишний раз правильные слова
                        out[-1] = prevWord.word #меняем предыдущое слово в связи с проверкой

                            
                out.append(newWord.word)
                prevWord = newWord
            
        else:
            newWord = morph.parse(word)[0] #стоп-слово или не является словом, оставим как есть
            prevWordT, newWordT, didChange = endCheck(prevWord, newWord)
            if didChange:
                if prevWordT != prevWord: #чтобы не менять лишний раз правильные слова
                    out[-1] = prevWord.word #меняем предыдущое слово в связи с проверкой
                
            out.append(newWord.word)
            prevWord = newWord
            
    # конец sentence loop
    out.append('\n')


#ВЫВОД
print("\n\n\nВЫВОД:\n")
textStr = TreebankWordDetokenizer().detokenize(out)

print(textStr)