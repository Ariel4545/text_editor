from socket import gethostname

# humane data
languages_list = (
            'Afrikaans', 'Albanian', 'Arabic', 'Armenian', ' Azerbaijani', 'Basque', 'Belarusian', 'Bengali', 'Bosnian',
            'Bulgarian', ' Catalan', 'Cebuano', 'Chichewa', 'Chinese', 'Corsican', 'Croatian', ' Czech', 'Danish',
            'Dutch',
            'English', 'Esperanto', 'Estonian', 'Filipino', 'Finnish', 'French', 'Frisian', 'Galician', 'Georgian',
            'German', 'Greek', 'Gujarati', 'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hindi', 'Hmong',
            'Hungarian',
            'Icelandic', 'Igbo', 'Indonesian', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kazakh', 'Khmer',
            'Kinyarwanda', 'Korean', 'Kurdish', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Lithuanian', 'Luxembourgish',
            'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Mongolian', 'Myanmar',
            'Nepali',
            'Norwegian''Odia', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Romanian', 'Russian', 'Samoan',
            'Scots Gaelic', 'Serbian', 'Sesotho', 'Shona', 'Sindhi', 'Sinhala', 'Slovak', 'Slovenian', 'Somali',
            'Spanish',
            'Sundanese', 'Swahili', 'Swedish', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Turkish', 'Turkmen',
            'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Vietnamese', 'Welsh', 'Xhosa''Yiddish', 'Yoruba', 'Zulu',
        )


city_list = ['Agra', 'buenos aires', 'Amsterdam', 'los angeles', 'Antalya', 'Athens', 'Atlanta', 'Auckland', 'Bali',
                     'Bangkok', 'Barcelona', 'Beijing', 'Berlin', 'Bogota', 'Boston', 'Brussels', 'Bucharest',
                     'Budapest', 'Cairo', 'hebron', 'mexico city', 'cape town', 'Chennai', 'Chicago',
                     'Copenhagen', 'washington D.C.', 'Dallas', 'tokyo', 'Delhi', 'san diego', 'Dubai', 'Dublin', 'Edinburgh', 'Edirne',
                     'alexandria', 'Florence', 'san francisco', 'Guangzhou', 'Hong kong', 'Honolulu', 'Houston',
                     'Istanbul', 'Jakarta', 'Janeiro', 'Jerusalem', 'Johannesburg', 'Kiev', 'hanoi', 'riyadh', 'mecca']
languages = {
            '0x409': ['English - United States', 'en'], '0x809': ['English - United Kingdom', 'en'],
            '0x0c09': ['English - Australia', 'en'], '0x2809': ['English - Belize', 'en'],
            '0x1009': ['English - Canada', 'en'], '0x2409': ['English - Caribbean', 'en'],
            '0x3c09': ['English - Hong Kong SAR', 'en'],
            '0x4009': ['English - India', 'en'], '0x3809': ['English - Indonesia', 'en'],
            '0x1809': ['English - Ireland', 'en'], '0x2009': ['English - Jamaica', 'en'],
            '0x4409': ['English - Malaysia', 'en'],
            '0x040c': ['French - France', 'fr'], '0x080c': ['French - Belgium', 'fr'],
            '0x407': ['German - Germany', 'de'], '0x0c07': ['German - Austria', 'de'],
            '0x1407': ['German - Liechtenstein', 'de'],
            '0x1007': ['German - Luxembourg', 'de'], '0x807': ['German - Switzerland', 'de'],
            '0x410': ['Italian - Italy', 'it'], '0x810': ['Italian - Switzerland', 'it'],
            '0x816': ['Portuguese - Portugal', 'pt'], '0x429': ['Farsi', 'fa'],
            '0x0c0a': ['Spanish - Spain (Modern Sort)', 'es'], '0x040a': ['Spanish - Spain (Traditional Sort)', 'es'],
        }
sr_supported_langs = {'English (US)' : 'en-US', 'English (UK)' : 'en-GB', 'Spanish (Spain)' : 'es-ES',
                                   'French': 'fr-FR', 'Russian' : 'ru', 'Arabic (Egypt)' : 'ar-EG' , 'Japanese' : 'ja',
                                   'Italian' : 'it-IT', 'Korean' : 'ko', 'Indonesian' : 'id', 'Hebrew' : 'he'
                                   }


# symbols translator
morse_code_dict = {'A': '.-', 'B': '-...',
                           'C': '-.-.', 'D': '-..', 'E': '.',
                           'F': '..-.', 'G': '--.', 'H': '....',
                           'I': '..', 'J': '.---', 'K': '-.-',
                           'L': '.-..', 'M': '--', 'N': '-.',
                           'O': '---', 'P': '.--.', 'Q': '--.-',
                           'R': '.-.', 'S': '...', 'T': '-',
                           'U': '..-', 'V': '...-', 'W': '.--',
                           'X': '-..-', 'Y': '-.--', 'Z': '--..',
                           '1': '.----', '2': '..---', '3': '...--',
                           '4': '....-', '5': '.....', '6': '-....',
                           '7': '--...', '8': '---..', '9': '----.',
                           '0': '-----', ', ': '--..--', '.': '.-.-.-',
                           '?': '..--..', '/': '-..-.', '-': '-....-',
                           '(': '-.--.', ')': '-.--.-', ' ': '/'
                           # ,'Á': '.--.-', 'Ä': '.-.-', 'É': '..-..', 'Ñ': '- - . - -',
                           # 'Ö': '- - - .', 'Ü': '. . - -'
                           }
'''+ can write an algo that can detected the order of the characters and config any value of combination'''
roman_dict = {
    'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000,
    'IV': 4, 'IX': 9, 'XL': 40, 'XC': 90, 'CD': 400, 'CM': 900}

# virtual keyboard
sym_n = ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                 '+', '-', '*', '^', '=', '<', '>', '[', ']',
                 '#', '!', '&', '?', ':', '/', '~')

syn_only = ('`', '_', '|', '$', '@', '£', '€', '¢', '¥', '§',
         '%', '°', r'\\', ';', '"', '\'', '®', '¿', 'ƒ',
         '√', '™', '©', '±', '≈', 'Ω', 'Φ')

# text decorators
base_characters = 'abcdefghijklmnopqrstuvwxyz .'
a = '..######..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n'
b = '..######..\n..#....#..\n..#####...\n..#....#..\n..######..\n\n'
c = '..######..\n..#.......\n..#.......\n..#.......\n..######..\n\n'
d = '..#####...\n..#....#..\n..#....#..\n..#....#..\n..#####...\n\n'
e = '..######..\n..#.......\n..#####...\n..#.......\n..######..\n\n'
f = '..######..\n..#.......\n..#####...\n..#.......\n..#.......\n\n'
g = '..######..\n..#.......\n..#####...\n..#....#..\n..#####...\n\n'
h = '..#....#..\n..#....#..\n..######..\n..#....#..\n..#....#..\n\n'
i = '..######..\n....##....\n....##....\n....##....\n..######..\n\n'
j = '..######..\n....##....\n....##....\n..#.##....\n..####....\n\n'
k = '..#...#...\n..#..#....\n..##......\n..#..#....\n..#...#...\n\n'
l = '..#.......\n..#.......\n..#.......\n..#.......\n..######..\n\n'
m = '..#....#..\n..##..##..\n..#.##.#..\n..#....#..\n..#....#..\n\n'
n = '..#....#..\n..##...#..\n..#.#..#..\n..#..#.#..\n..#...##..\n\n'
o = '..######..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n'
p = '..######..\n..#....#..\n..######..\n..#.......\n..#.......\n\n'
q = '..######..\n..#....#..\n..#.#..#..\n..#..#.#..\n..######..\n\n'
r = '..######..\n..#....#..\n..#.##....\n..#...#...\n..#....#..\n\n'
s = '..######..\n..#.......\n..######..\n.......#..\n..######..\n\n'
t = '..######..\n....##....\n....##....\n....##....\n....##....\n\n'
u = '..#....#..\n..#....#..\n..#....#..\n..#....#..\n..######..\n\n'
v = '..#....#..\n..#....#..\n..#....#..\n...#..#...\n....##....\n\n'
w = '..#....#..\n..#....#..\n..#.##.#..\n..##..##..\n..#....#..\n\n'
x = '..#....#..\n...#..#...\n....##....\n...#..#...\n..#....#..\n\n'
y = '..#....#..\n...#..#...\n....##....\n....##....\n....##....\n\n'
z = '..######..\n......#...\n.....#....\n....#.....\n..######..\n\n'
sp = '&&&&&&\n&&&&&&\n&&&&&&\n&&&&&&\n\n'
dot = '----..----\n\n'
bash_alph = (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z,
                   sp, dot)
ascii_dict_bash = {}
for index, ascii_character in enumerate(bash_alph):
    ascii_dict_bash[base_characters[index]] = ascii_character

bin_a = (
    '000000000000\n000111111000\n011000000110\n011000000110\n011111111110\n011000000110\n011000000110\n011000000110\n\n')
bin_b = (
    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011000000110\n011000000110\n011111111000\n\n')
bin_c = (
    '000000000000\n000111111000\n011000000110\n011000000000\n011000000000\n011000000000\n011000000110\n000111111000\n\n')
bin_d = (
    '000000000000\n011111111000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n011111111000\n\n')
bin_e = (
    '000000000000\n011111111110\n011000000000\n011000000000\n011111111100\n011000000000\n011000000000\n011111111110\n\n')
bin_f = (
    '000000000000\n011111111110\n011000000000\n011000000000\n011111111100\n011000000000\n011000000000\n011000000000\n\n')
bin_g = (
    '000000000000\n000111111000\n011000000110\n011000000000\n011000000000\n011000011110\n011000000110\n000111111000\n\n')
bin_h = (
    '000000000000\n011000000110\n011000000110\n011000000110\n011111111110\n011000000110\n011000000110\n011000000110\n\n')
bin_i = (
    '000000000000\n000111111000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000111111000\n\n')
bin_j = (
    '000000000000\n000001111110\n000000011000\n000000011000\n000000011000\n000000011000\n011000011000\n000111100000\n\n')
bin_k = (
    '000000000000\n011000000110\n011000011000\n011001100000\n011110000000\n011001100000\n011000011000\n011000000110\n\n')
bin_l = (
    '000000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011000000000\n011111111110\n\n')
bin_m = (
    '000000000000\n011000000110\n011110011110\n011001100110\n011001100110\n011000000110\n011000000110\n011000000110\n\n')
bin_n = (
    '000000000000\n011000000110\n011000000110\n011110000110\n011001100110\n011000011110\n011000000110\n011000000110\n\n')
bin_o = (
    '000000000000\n000111111000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n000111111000\n\n')
bin_p = (
    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011000000000\n011000000000\n011000000000\n\n')
bin_q = (
    '000000000000\n000111111000\n011000000110\n011000000110\n011000000110\n011001100110\n011000011000\n000111100110\n\n')
bin_r = (
    '000000000000\n011111111000\n011000000110\n011000000110\n011111111000\n011001100000\n011000011000\n011000000110\n\n')
bin_s = (
    '000000000000\n000111111110\n011000000000\n011000000000\n000111111000\n000000000110\n000000000110\n011111111000\n\n')
bin_t = (
    '000000000000\n011111111110\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n\n')
bin_u = (
    '000000000000\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n011000000110\n000111111000\n\n')
bin_v = (
    '000000000000\n011000000110\n011000000110\n011000000110\n011000000110\n000110011000\n000110011000\n000001100000\n\n')
bin_w = (
    '000000000000\n011000000110\n011000000110\n011000000110\n011001100110\n011001100110\n011001100110\n000110011000\n\n')
bin_x = (
    '000000000000\n011000000110\n011000000110\n000110011000\n000001100000\n000110011000\n011000000110\n011000000110\n\n')
bin_y = (
    '000000000000\n011000000110\n011000000110\n000110011000\n000001100000\n000001100000\n000001100000\n000001100000\n\n')
bin_z = (
    '000000000000\n011111111110\n000000000110\n000000011000\n000001100000\n000110000000\n011000000000\n011111111110\n\n')
bin_sp = (
    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n\n')
bin_n0 = (
    '000000000000\n000111111000\n011000000110\n011000011110\n011001100110\n011110000110\n011000000110\n000111111000\n\n')
bin_n1 = (
    '000000000000\n000001100000\n000111100000\n000001100000\n000001100000\n000001100000\n000001100000\n000111111000\n\n')
bin_n2 = (
    '000000000000\n000111111000\n011000000110\n000000000110\n000000011000\n000001100000\n000110000000\n011111111110\n\n')
bin_n3 = (
    '000000000000\n011111111110\n000000011000\n000001100000\n000000011000\n000000000110\n011000000110\n000111111000\n\n')
bin_n4 = (
    '000000000000\n000000011000\n000001111000\n000110011000\n011000011000\n011111111110\n000000011000\n000000011000\n\n')
bin_n5 = (
    '000000000000\n011111111110\n011000000000\n011111111000\n000000000110\n000000000110\n011000000110\n000111111000\n\n')
bin_n6 = (
    '000000000000\n000001111000\n000110000000\n011000000000\n011111111000\n011000000110\n011000000110\n000111111000\n\n')
bin_n7 = (
    '000000000000\n011111111110\n000000000110\n000000011000\n000001100000\n000110000000\n000110000000\n000110000000\n\n')
bin_n8 = (
    '000000000000\n000111111000\n011000000110\n011000000110\n000111111000\n011000000110\n011000000110\n000111111000\n\n')
bin_n9 = (
    '000000000000\n000111111000\n011000000110\n011000000110\n000111111110\n000000000110\n000000011000\n000111100000\n\n')
bin_s0 = (
    '000000000000\n000111111000\n011000000110\n000000000110\n000000011000\n000001100000\n000000000000\n000001100000\n\n')
bin_s1 = (
    '000000000000\n000001100000\n000001100000\n000001100000\n000001100000\n000001100000\n000000000000\n000001100000\n\n')
bin_s2 = (
    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000001100000\n000001100000\n\n')
bin_s3 = (
    '000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000000000000\n000001100000\n\n')
bin_s4 = (
    '000000000000\n000000000000\n000000000000\n000000000000\n001111111100\n000000000000\n000000000000\n000000000000\n\n')
bin_s5 = (
    '000000000000\n000000000000\n000001100000\n000001100000\n011111111110\n000001100000\n000001100000\n000000000000\n\n')

binary_alph = (bin_a, bin_b, bin_c, bin_d, bin_e, bin_f, bin_g, bin_h, bin_i, bin_j, bin_k, bin_l, bin_m, bin_n, bin_o,
              bin_p, bin_q, bin_r, bin_s, bin_t, bin_u, bin_v, bin_w, bin_x, bin_y, bin_z,
                   bin_sp, bin_n0, bin_n1, bin_n2, bin_n3, bin_n4, bin_n5, bin_n6, bin_n7, bin_n8, bin_n9,
                   bin_s0, bin_s1, bin_s2, bin_s3, bin_s4, bin_s5, bin_s5)
binary_characters = base_characters + ' 0123456789?!,.-#'
ascii_dict_binary = {}
for index, ascii_character in enumerate(binary_alph):
    ascii_dict_binary[binary_characters[index]] = ascii_character

'''+ extreme idea for the list'''
# ascii_alph = (
asterisk_a = ('  ******  \n  *    *  \n  ******  \n  *    *  \n  *    *  \n\n')
asterisk_b = ('  ******  \n  *     * \n  ******  \n  *     * \n  ******  \n\n')
asterisk_c = ('  ******  \n  *       \n  *       \n  *       \n  ******  \n\n')
asterisk_d = ('  *****   \n  *    *  \n  *    *  \n  *    *  \n  *****   \n\n')
asterisk_e = ('  ******  \n  *       \n  *****   \n  *       \n  ******  \n\n')
asterisk_f = ('  ******  \n  *       \n  *****   \n  *       \n  *       \n\n')
asterisk_g = ('  *******  \n  *        \n  *   ***  \n  *      * \n  *******  \n\n')
asterisk_h = ('  *     *  \n  *     *  \n  *******  \n  *     *  \n  *     *  \n\n')
asterisk_i = ('  **   \n  **   \n  **   \n  **   \n  **   \n\n')
asterisk_j = ('  ******  \n      **  \n      **  \n  **  **  \n  ******  \n\n')
asterisk_k = ('  *   *  \n  *  *   \n  * *    \n  *  *   \n  *   *  \n\n')
asterisk_l = ('  *     \n  *     \n  *     \n  *     \n  ******\n\n')
asterisk_m = ('  *       *\n  **     **\n  *  *  * *\n  *   **  *\n  *       *\n\n')
asterisk_n = ('  **   *  \n  **   *  \n  * *  *  \n  *  * *  \n  *   **  \n\n')
asterisk_o = ('   *****   \n  *     *  \n  *     *  \n  *     *  \n   *****   \n\n')
asterisk_p = ('  ******  \n  *     * \n  ******  \n  *       \n  *       \n\n')
asterisk_q = ('   ******  \n  *      * \n   ******  \n        *  \n        *  \n\n')
asterisk_r = ('  ******  \n  *     * \n  * ***   \n  *  *    \n  *    *  \n\n')
asterisk_s = ('  ******  \n  *       \n  ******  \n       *  \n  ******  \n\n')
asterisk_t = ('  ******\n    **  \n    **  \n    **  \n    **  \n\n')
asterisk_u = ('  *     *  \n  *     *  \n  *     *  \n  *     *  \n   *****   \n\n')
asterisk_v = ('  *    *  \n  *    *  \n  *    *  \n   *  *   \n    **    \n\n')
asterisk_w = ('  *       *  \n  *  * *  *  \n  * *   * *  \n  **     **  \n  **     **  \n\n')
asterisk_x = ('  *     *  \n   *   *   \n    * *    \n   *   *   \n  *     *  \n\n')
asterisk_y = ('  *     * \n   *  *   \n    **    \n    **    \n    **    \n\n')
asterisk_z = ('   ******\n       **\n    ***  \n  **     \n  ****** \n\n')
asterisk_sp = ('..........\n..........\n..........\n..........\n\n')
asterisk_dot = ('....\n....\n....\n.....\n\n')
# )
'''+ loop with an ABC list'''


characters = base_characters + '.'
asterisk_alph = (asterisk_a, asterisk_b, asterisk_c, asterisk_d, asterisk_e, asterisk_f, asterisk_g, asterisk_h, asterisk_i,
              asterisk_j, asterisk_k, asterisk_l, asterisk_m, asterisk_n, asterisk_o, asterisk_p, asterisk_q, asterisk_r,
              asterisk_s, asterisk_t, asterisk_u, asterisk_v, asterisk_w, asterisk_x, asterisk_y, asterisk_z, asterisk_sp,
                   asterisk_dot)

ascii_dict_asterisk = {}
for index, ascii_character in enumerate(asterisk_alph):
    ascii_dict_asterisk[base_characters[index]] = ascii_character

characters_dict = {'asterisk' : (ascii_dict_asterisk, asterisk_alph, 5), 'binary' : (ascii_dict_binary, binary_alph, 8),
'bash' : (ascii_dict_bash, bash_alph, 5)}


# binding of events
filea_list = ['<Control-o>', '<Control-O>', '<Control-Key-s>', '<Control-Key-S>', '<Control-Key-n>',
                      '<Control-Key-N>', '<Control-Key-p>', '<Control-Key-P>', '<Alt-Key-d>', '<Alt-Key-D>']
typef_list = ['<Control-Key-B>', '<Control-Key-b>', '<Control-Key-i>', '<Control-Key-I>',
              '<Control-Key-u>', '<Control-Key-U>']
editf_list = ['<Control-Key-f>', '<Control-Key-F>', '<Control-Key-h>', '<Control-Key-H>',
              '<Control-Key-g>', '<Control-Key-G>']
textt_list = ['<Control-Shift-Key-j>', '<Control-Shift-Key-J>', '<Control-Shift-Key-u>', '<Control-Shift-Key-U>',
              '<Control-Shift-Key-r>', '<Control-Shift-Key-R>', '<Control-Shift-Key-c>', '<Control-Shift-Key-C>']
win_list = ['<F11>', '<Control-Key-t>', '<Control-Key-T>']
autof_list = ['<KeyPress>', '<KeyRelease>']
right_aligned_l = ('Arabic', 'Hebrew', 'Persian', 'Pashto', 'Urdu', 'Kashmiri', 'Sindhi')

# file's extensions
text_extensions = (('Text Files', '*.txt'), ('HTML Files', '*.html'), ('Python Files', '*.py'))
img_extensions = (('PNG', '*.png'), ('JPG', '*.jpg'), ('JPEG Files', '*.jpeg'))

# non-grouped
characters_str = ('Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Z',
                     'X', 'C', 'V', 'B', 'N', 'M')
op_msgs = ('Hello world!', '^-^', 'What a beautiful day!', 'Welcome!', '', 'Believe in yourself!',
                       'If I did it you can do way more than that', 'Don\'t give up!',
                       'I\'m glad that you are using my Text editor (:', 'Feel free to send feedback',
                       f'hi {gethostname()}')

# Base packages (your canonical list)
library_list = [
    'bs4', 'emoji', 'keyboard', 'matplotlib', 'names', 'pandas', 'PIL',
    'pyaudio', 'pydub', 'ffmpeg-downloader', 'PyPDF2', 'nltk', 'PyDictionary',
    'tkinter-tooltip', 'pyperclip', 'pytesseract', 'pyttsx3', 'pywin32', 'spacy',
    'SpeechRecognition', ' ssl', 'win32print', 'fast-autocomplete[levenshtein]',
    'textblob', 'urllib', 'webbrowser', 'wikipedia', 'win32api', 'requests', 'numexpr'
]

# Optional extras (kept here so "most" lives in this file—
# you can append more in the main file if you must)
library_optional = [
    'openai',
    'youtube-transcript-api',
    'pyshorteners',
    'cryptography',
    'rsa',
    'GitPython',
    'emoticon',
    'tkhtmlview',
    'python-docx',
    'tktooltip'
]

# Aliases and canonical names for pip (no runtime, pure data)
# Keys are lowercased; values are the canonical pip name or version-pinned spec
library_alias_map = {
    'pil': 'Pillow',
    'pillow': 'Pillow',
    'pypdf2': 'PyPDF2',
    'py-pdf2': 'PyPDF2',
    'tkinter-tooltip': 'tkinter-tooltip',   # this is a real project
    'tktooltip': 'tktooltip',               # different project, included only if used
    'ffmpeg-downloader': 'ffmpeg-downloader',
    # Known better pin for many envs:
    'googletrans': 'googletrans==4.0.0rc1',
}

# Things we should NOT attempt to pip install (stdlib or core)
# all checked as lowercased tokens
library_blocklist = {
    'urllib', 'webbrowser', 'email', 'ssl', 'sys', 'tkinter',
}

# Optional pins (explicit versions you prefer, if needed)
# Keys are lowercased canonical names
# Values are exact spec strings (e.g., 'package==1.2.3' or 'package>=1.0')
library_pins = {
    # 'numpy': 'numpy==1.26.4',
    # 'spacy': 'spacy>=3.7',
}

data = {'night_mode': False, 'status_bar': True, 'file_bar': True, 'cursor': 'xterm',
                     'style': 'clam',
                     'word_wrap': True, 'reader_mode': False, 'auto_save': True, 'relief': 'ridge',
                     'transparency': 100, 'toolbar': True, 'open_last_file': '', 'text_twisters': False,
                     'night_type': 'black', 'preview_cc': False, 'fun_numbers': True, 'usage_report': False,
                     'check_version': False, 'window_c_warning' : True, 'allow_duplicate': False}

special_files = (('excel', '*.xlsx'), ('csv', '*.csv'), ('pdf', '*.pdf')
																 , ('json', '*.json'), ('xml', '*.xml'),
																 ('all', '*.*'))

night_mode_colors = {'black' : ['#110022', '#373737', '#27374D', 'green'], 'blue' : ['#041C32', '#04293A', '#064663', '#ECB365']
    , 'default' : ['SystemButtonFace', 'SystemButtonFace', 'SystemButtonFace', 'black']}


function_items = [
    'Get nouns', 'Get verbs', 'Get adjectives', 'Get adverbs', 'Get pronouns',
    'Get stop words',
    'Entity recognition', 'Dependency tree', 'Lemmatization', 'Most common words',
    'Get names (persons)', 'Get phone numbers', 'Extract emails', 'Extract URLs', 'Extract IP addresses',
    'Key phrases (noun chunks)', 'N-grams (2–3)', 'Sentence split', 'POS distribution', 'Sentiment (VADER)',
]

function_map = {
    'Get nouns': 'NOUN', 'Get verbs': 'VERB', 'Get adjectives': 'ADJ', 'Get adverbs': 'ADV', 'Get pronouns': 'PRON',
    'Get stop words': 'stop words',
    'Entity recognition': 'entity recognition', 'Dependency tree': 'dependency', 'Lemmatization': 'lemmatization',
    'Most common words': 'most common words',
    'Get names (persons)': 'FULL_NAME', 'Get phone numbers': 'PHONE_NUMBER',
    'Extract emails': 'EMAILS', 'Extract URLs': 'URLS', 'Extract IP addresses': 'IP_ADDRESSES',
    'Key phrases (noun chunks)': 'KEY_PHRASES', 'N-grams (2–3)': 'NGRAMS',
    'Sentence split': 'SENTENCE_SPLIT', 'POS distribution': 'POS_DISTRIBUTION', 'Sentiment (VADER)': 'SENTIMENT',
}
