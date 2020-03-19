#!/usr/bin/env python3
"""@author TELEMAC-MASCARET Consortium

   @brief Generate doxygen documentation of telemac-mascaret
"""
from __future__ import print_function
# _____          ___________________________________________________
# ____/ Imports /__________________________________________________/
#
# ~~> dependencies towards standard python
import sys
import re
from os import path, walk, chdir
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import subprocess as sp
# ~~> dependencies towards other pytel/modules
from compilation.parser_fortran import scan_sources, parse_doxy_wrap
from utils.files import get_file_content, put_file_content, create_directories
from utils.messages import svn_banner
from config import add_config_argument, update_config, CFGS

# _____                  ___________________________________________
# ____/ General Toolbox /__________________________________________/
#

def create_doxygen(ifile, ilines, lname, tree):
    """
    Update of content for the Documentation of TELEMAC preparing for
    Doxygen

    @param ifile (string) file from where export the ilines for the
           Documentation of TELEMAC preparing for Doxygen
    @param ilines(list) content line file
    @param lname (string) Name of the library withinwhich the name is
    @param tree (dico) tree of dependencies come from the compilation

    @return olines (list) content line in output of new DOXYGEN
    """
    # ~~ Parsers ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    olines = []

    print('    +>  '+path.basename(ifile), end='')
    for name, subname, doxy, body in parse_doxy_wrap(ilines):
        print(subname+' '+name, end='')
        who = tree[lname][subname]

        # ~~ General
        olines.append(ifile + '\n!')

        # ~~ Module
        olines.append('!> @par Module: '+who['libname']+'\n!')

        for doc in doxy:
            # ~~ Brief
            if doc[0] == 'brief':
                line = '!> @brief\n!> ' + '\n!> '.join(doc[1])
                line.replace('\n!> \n', '\n!> <br><br>\n')
                olines.append(line+'\n!')

            # ~~ User Defined Information
            if doc[0] in ['bug', 'note', 'warn', 'refs', 'code']:
                if doc[0] == 'note':
                    line = '!> @note\n!> ' + '\n!> '.join(doc[1])
                    line.replace('\n!> \n', '\n!> <br><br>\n')
                    olines.append(line+'\n!')
                if doc[0] == 'bug':
                    line = '!> @bug\n!> ' + '\n!> '.join(doc[1])
                    line.replace('\n!> \n', '\n!> <br><br>\n')
                    olines.append(line+'\n!')
                if doc[0] == 'warn':
                    line = '!> @warning\n!> ' + '\n!> '.join(doc[1])
                    line.replace('\n!> \n', '\n!> <br><br>\n')
                    olines.append(line+'\n!')
                if doc[0] == 'refs':
                    line = '!> @reference\n!> ' + '\n!> '.join(doc[1])
                    line.replace('\n!> \n', '\n!> <br><br>\n')
                    olines.append(line+'\n!')
                if doc[0] == 'code':
                    line = '!> @code\n!> ' + '\n!> '.join(doc[1])
                    line.replace('\n!> \n', '\n!> <br><br>\n')
                    olines.append(line + '\n!> @endcode\n!')

        # ~~ Final Uses ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if who['uses'] != {}:
            line = '!> @par Use(s)\n!><br>' + \
                   ', '.join(sorted(who['uses'].keys()))
            olines.append(line+'\n!')

        # ~~ Final Variables ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if who['args'] != [] or who['vars']['use'] != {} or \
            who['vars']['cmn'] != [] or who['vars']['dec'] != [] or \
            who['vars']['als'] != []:
            line = '!> @par Variable(s)\n!>  <br><table>'
            olines.append(line)

            # ~~ Arguments
            if who['args'] != []:
                line = '!>     <tr><th> Argument(s)\n!>    </th><td> ' + \
                         ', '.join(sorted(who['args'])) + '\n!>   </td></tr>'
                olines.append(line)
            # ~~ Uses
            if who['vars']['use'] != {}:
                line = '!>     <tr><th> Use(s)\n!>    </th><td>'
                for used1 in who['vars']['use']:
                    used = []
                    for used2 in who['vars']['use'][used1]:
                        used.append('\n!> @link ' + used1 + '::' + \
                                        used2 + ' ' + used2 + '@endlink')
                    line = line + '<hr>\n!> ' + used1 + \
                             ' :<br>' + ', '.join(sorted(used))
                line = line.replace('<td><hr>\n', '<td>\n') + \
                                    '\n!>   </td></tr>'
                olines.append(line)

            # ~~ Commons
            if who['vars']['cmn'] != []:
                line = '!>     <tr><th> Common(s)\n!>    </th><td>'
                for cmn in who['vars']['cmn']:
                    line = line + '<hr>\n!> ' + cmn[0] + ' : ' + \
                                  ', '.join(cmn[1])
                line = line.replace('<td><hr>\n', '<td>\n') + \
                                    '\n!>   </td></tr>'
                olines.append(line)

            # ~~ Declars
            if who['vars']['dec'] != []:
                line = '!>     <tr><th> Internal(s)\n!>    </th><td> ' + \
                       ', '.join(sorted(who['vars']['dec'])) + \
                       '\n!>   </td></tr>'
                olines.append(line)

            # ~~ Aliases
            if who['vars']['als'] != []:
                line = '!>     <tr><th> Alias(es)\n!>    </th><td> ' + \
                       ', '.join(sorted(who['vars']['als'])) + \
                       '\n!>   </td></tr>'
                olines.append(line)

            line = '!>     </table>\n!'
            olines.append(line)

        # ~~ Final Calls ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if who['calls'] != {} or who['functions'] != []:
            line = '!> @par Call(s)\n!>  <br><table>'
            olines.append(line)
            if who['calls'] != {}:
                line = '!>     <tr><th> Known(s)\n!>    </th><td> ' + \
                         '(), '.join(sorted(who['calls'].keys())) + \
                         '()\n!>   </td></tr>'
                olines.append(line)
            if who['functions'] != []:
                line = '!>     <tr><th> Unknown(s)\n!>    </th><td> ' + \
                       ', '.join(sorted(who['functions'])) + \
                       '\n!>   </td></tr>'
                olines.append(line)
            line = '!>     </table>\n!'
            olines.append(line)

        # ~~ Final Called ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if who['called'] != []:
            line = '!> @par Called by\n!><br>' + \
                   '(), '.join(sorted(who['called'])) + '()\n!'
            olines.append(line)

        # ~~ Final History ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for doc in doxy:
            # ~~ Other pars
            if doc[0] == 'para':
                line = '!> @par ' + '\n!> '.join(doc[1])
                line.replace('\n!> \n', '\n!> <br><br>\n')
                olines.append(line+'\n')
            # ~~ Result
            if doc[0] == 'result':
                line = '!> @par Result ' + '\n!> '.join(doc[1])
                olines.append(line+'\n!')

        # ~~ Final History ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        hist = False
        for doc in doxy:
            if doc[0] == 'history':
                hist = True
        if hist:
            olines.append('!> @par Development history')
            olines.append('!>   <br><table>')
            olines.append('!> <tr><th> Release </th><th> Date </th>'\
                          '<th> Author </th><th> Notes </th></tr>')
            for doc in doxy:
                if doc[0] == 'history':
                    olines.append('!>  <tr><td><center> ' + doc[1][2] + \
                                  ' </center>')
                    olines.append('!>    </td><td> ' + doc[1][1])
                    olines.append('!>    </td><td> ' + doc[1][0])
                    if len(doc[1]) > 3:
                        olines.append('!>    </td><td> ' + doc[1][3])
                    else:
                        olines.append('!>    </td><td> ')

                        raise Exception(\
                          '\nHistory comment missing in:'
                          ' {}\n\n{}'.format(subname, doc))

                    olines.append('!>   </td></tr>')
            olines.append('!>   </table>\n!')

        # ~~ Unchanged ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        for line in body:
            olines.append(line)

    print('')
    return olines


def replace_doxygen(doxydocs):
    """
        Replace all the information required for the Documentation of TELEMAC
        (in htlm) preparing for Doxygen

        @param doxydocs(string) path to search the command of DOXYGENE
    """

    i_txt_lst = [('<!DOCTYPE HTML PUBLIC', '<BODY BGCOLOR="#FFFFFF">'),
                 ('<DIV class="div-page">', '<hr>'),
                 ('<div class="header">', '<div class="summary">'),
                 ('<hr>\n<div class="div-footer">', '</html>'),
                 ('<dl class="user"><dt><', '>'), \
                 ('</b></dt><d', 'd><br/>')]
    o_txt_lst = [r"""<!DOCTYPE install PUBLIC "-//Joomla! 2.5//DTD template 1.0//EN" "http://www.joomla.org/xml/dtd/1.6/template-install.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" dir="ltr">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <meta name="keywords" content="open, telemac, mascaret, hydraulique, surface libre, houle, vague, hydraulic, free surface, wave, sediment" />
        <meta name="robots" content="index, follow" />
        <meta name="date" content="2013-07-24T16:49:04+0100"/>
        <meta name="description" content="The open TELEMAC-MASCARET system is a set of software for free surface numerical modelling of:\n* 2D, 3D Hydrodynamics,\n* Sediment (sand and muds),\n* Waves." />
        <title>The open TELEMAC-MASCARET system: 2D, 3D hydrodynamics sediment waves simulation system</title>
        <link rel="shortcut icon" href="./images/favicon.ico" type="image/vnd.microsoft.icon" />
        <script src="./images/jquery-1.4.2.min.js" type="text/javascript"></script>
        <link rel="stylesheet" href="./images/system.css" type="text/css" />
        <link rel="stylesheet" href="./images/position.css" type="text/css" media="screen,projection" />
        <link rel="stylesheet" href="./images/layout.css" type="text/css" media="screen,projection" />
        <link rel="stylesheet" href="./images/general.css" type="text/css" />
        <link rel="stylesheet" href="./images/principal.css" type="text/css" />
        <style type="text/css">
        #ahgalleryOTconsortium { margin-left: auto; margin-right: auto; margin-top: 0px !important; margin-bottom: 0px !important; width: 1000px; }
        #ahgalleryOTconsortium ul.hover_block0, #ahgalleryOTconsortium ul.hover_block1, #ahgalleryOTconsortium ul.hover_block2 { display: block; overflow: hidden; padding-top: 20px; padding-left: 2px; background: transparent; margin-left: 2px; margin-top: 0 !important; margin-bottom: 0 !important; }
        #ahgalleryOTconsortium ul.bottom_block { padding-bottom: 20px ; }
        #ahgalleryOTconsortium ul.hover_block0 li.item, #ahgalleryOTconsortium ul.hover_block1 li.item, #ahgalleryOTconsortium ul.hover_block2 li.item { margin-left: 0; padding-left: 0; list-style:none; list-style-position: inside; float:left; background: transparent; width: 150px; position: relative; }
        #ahgalleryOTconsortium ul.hover_block0 li a.teaser, #ahgalleryOTconsortium ul.hover_block1 li a.teaser , #ahgalleryOTconsortium ul.hover_block2 li a.teaser{ display: block; position: relative; overflow: hidden; height: 60px; width: 130px; padding: 1px; }
        #ahgalleryOTconsortium ul.hover_block0 li div.teaser, #ahgalleryOTconsortium ul.hover_block1 li div.teaser , #ahgalleryOTconsortium ul.hover_block2 li div.teaser { display: block; position: relative; overflow: hidden; height: 60px; width: 140px; padding: 1px; }
        #ahgalleryOTconsortium ul.hover_block0 li img.overlay, #ahgalleryOTconsortium ul.hover_block1 li img.overlay, #ahgalleryOTconsortium ul.hover_block2 li img.overlay { margin: 0; position: absolute; top: 5px; left: 0; border: 0; }
        </style>
        <script type="text/javascript" src="./images/hide.js"></script>
        <script type="text/javascript">
            window.addEvent(\'load\', function() {
                new JCaption(\'img.caption\');
            });
            window.addEvent(\'domready\', function() {
                $$(\'.hasTip\').each(function(el) {
                    var title = el.get(\'title\');
                    if (title) {
                        var parts = title.split(\'::\', 2);
                        el.store(\'tip:title\', parts[0]);
                        el.store(\'tip:text\', parts[1]);
                }});
                var JTooltips = new Tips($$(\'.hasTip\'), \
                                { maxTitleChars: 50, fixed: false});
            });
        </script>
        <link href="./images/tabsVTK.css" rel="stylesheet" type="text/css"/>
        <link href="./images/searchVTK.css" rel="stylesheet" type="text/css"/>
        <script type="text/javaScript" src="./images/searchVTK.js"></script>
        <link href="./images/doxygenVTK.css" rel="stylesheet" type="text/css"/>
        </HEAD>
    <BODY BGCOLOR="#FFFFFF">""",\
        """<div id="all">
     <div id="header">
          <div class="logoheader">
                <h1 id="logo">open TELEMAC-MASCARET               <span class="header1">The mathematically superior suite of solvers</span></h1>
            </div>
            <div class="bar-top" >
            <ul class="menu">
             <li><a href="http://www.opentelemac.org/" ><img src="./images/OTM_Home-icon_15pix_212-118-0.png" alt="Home" /><span class="image-title">Home</span> </a></li>
         <li><a href="http://www.opentelemac.org/index.php/contact2"><img src="./images/OTM_Mail-icon_15pix_212-118-0.png" alt="Contact"/><span class="image-title">CONTACT</span> </a></li>
         <li><span class="separator"><img src="./images/OTM_transparent_15x080pix.png" /><img src="./images/OTM_transparent_15x080pix.png" /></span></li>
         <li><a href="http://www.opentelemac.org/index.php/community"><span class="image-title">COMMUNITY</span> </a></li>
         <li><a href="http://www.opentelemac.org/index.php/user-conference"><span class="image-title">CONFERENCE</span> </a></li>
         <li><a href="http://www.opentelemac.org/index.php/download"><span class="image-title">DOWNLOAD</span> </a></li>
             <li><a href="http://docs.opentelemac.org/" style="color:#333;background:#ffd1a3;padding:10px;"><span class="image-title">DOXY DOCS</span> </a></li>
         <li><a href="http://www.opentelemac.org/index.php/kunena"><span class="image-title">FORUM</span> </a></li>
             <li><a href="http://wiki.opentelemac.org/doku.php"><span class="image-title">WIKI</span> </a></li>
                </ul>
                </div>
                </div>

        <!-- Generated by Doxygen 1.7.0 -->
        <script type="text/javascript">
        function hasClass(ele,cls) {
          return ele.className.match(new RegExp('(\\s|^)'+cls+'(\\s|$)'));
        }
        function addClass(ele,cls) {
          if (!this.hasClass(ele,cls)) ele.className += " "+cls;
        }
        function removeClass(ele,cls) {
          if (hasClass(ele,cls)) {
             var reg = new RegExp('(\\s|^)'+cls+'(\\s|$)');
             ele.className=ele.className.replace(reg,' ');
          }
        }
        function toggleVisibility(linkObj) {
         var base = linkObj.getAttribute('id');
         var summary = document.getElementById(base + '-summary');
         var content = document.getElementById(base + '-content');
         var trigger = document.getElementById(base + '-trigger');
         if ( hasClass(linkObj,'closed') ) {
            summary.style.display = 'none';
            content.style.display = 'block';
            trigger.src = 'open.png';
            removeClass(linkObj,'closed');
            addClass(linkObj,'opened');
         } else if ( hasClass(linkObj,'opened') ) {
            summary.style.display = 'block';
            content.style.display = 'none';
            trigger.src = 'closed.png';
            removeClass(linkObj,'opened');
            addClass(linkObj,'closed');
         }
         return false;
        }
        </script>
        <br>""",\
        """<div  id="main" >
            <div  class="header" >
            <div  class="summary" >""",\
            """<br>
        </div></div>
                    <h2 class="unseen">Generated on Fri Aug 31 2013 18:12:58 by S.E.Bourban (HRW) using <A href="http://www.doxygen.org/index.html"><img class="footer" width=70px src="doxygen.png" alt="doxygen"/></A> 1.7.0</h2>
                    <div  id="footer-outer" ><div id="footer-inner"><div id="bottom"><div class="box box1"><div class="moduletable">
                    <script type="text/javascript">
                  jQuery.noConflict();
          jQuery(document).ready(function($)
            {
             $('#ahgalleryOTconsortium ul.hover_block0 li.item').hover(function(){
              $(this).find('img.overlay').animate({top:'60px'},{queue:false,duration:500});
             }, function(){
              $(this).find('img.overlay').animate({top:'5px'},{queue:false,duration:500});
             });
          });
          </script>
                    <div id="ahgalleryOTconsortium">
                        <ul class="hover_block0 bottom_block">
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://www.arteliagroup.com/" target="_blank"><img class="overlay" src="./images/Sogreah-Artelia.jpg" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">Artelia</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://www.baw.de/de/index.php.html" target="_blank"><img class="overlay" src="./images/logo_baw.png" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">BundesAnstalt fur Wasserbau</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://www.cetmef.equipement.gouv.fr/" target="_blank"><img class="overlay" src="./images/logo_cetmef_v2.png" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">CETMEF</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://www.stfc.ac.uk/About%20STFC/45.aspx" target="_blank"><img class="overlay" src="./images/logo_Daresbury_v3.gif" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">Daresbury Laboratory</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://research.edf.com/research-and-innovation-44204.html&amp;tab=44205" target="_blank"><img class="overlay" src="./images/logo_edfR&D.jpg" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">EDF R&D</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                            <li class="item"><a class="teaser" style="background-color:transparent !important;  font-weight: normal; text-decoration: none;" href="http://www.hrwallingford.com" target="_blank"><img class="overlay" src="./images/logo_HRW.png" alt="" />
                                <span style="color:grey; font-size: 14px; font-weight: bold; line-height: 18px; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em; display: block; text-align: center;">HR Wallingford</span>
                                <span style="color:white; display: block; font-size: 12px; font-weight: normal; font-family: arial; margin-bottom: 0.5em; margin-top: 0.5em;"></span></a></li>
                        </ul></div>
          <div class="clr"></div>
         </div></div>
         </div></div>
                    <div id="footer-sub"><div id="footer">
                        <ul class="menu">
                            <li class="item-187"><a href="http://www.opentelemac.org/index.php/forum-rules" >Forum rules</a></li>
                            <li class="item-111"><a href="http://www.opentelemac.org/index.php/licence" >Licence</a></li>
                            <li class="item-112"><a href="http://www.opentelemac.org/index.php/privacy" >Privacy</a></li>
                            <li class="item-112"><a href="http://www.opentelemac.org/index.php/terms-and-conditions" >Terms &amp; Conditions</a></li>
                        </ul>
                    </div>
         </div></div>
        </body></html>""",\
        '<dl class="user"><dt><h3><b>',\
        '</b></h3></dt><dd><br/>']

    text = r'(?P<before>[\s\S]*?)(?P<text>%s)(?P<after>[\s\S]*)'
    if path.exists(doxydocs):
        dirpath, _, filenames = next(walk(doxydocs))
        for fle in filenames:
            _, tail = path.splitext(fle)
            if tail == '.html':
                print('    +> '+fle)
                lines = ''.join(get_file_content(path.join(dirpath, fle)))
                proc = True
                while proc:
                    proc = False
                    for itext, otext in zip(i_txt_lst, o_txt_lst):
                        proc0 = re.match(re.compile(text%(itext[0]), re.I), \
                                         lines)
                        if proc0:
                            bfr = proc0.group('before')
                            proc1 = re.match(re.compile(text%(itext[1]), re.I),
                                             proc0.group('after'))
                            if proc1:
                                proc = True
                                aftr = proc1.group('after')
                                lines = bfr + otext + aftr
                                #print('replacing: ',
                                #      proc0.group('text')+ \
                                #      proc1.group('before'))
                put_file_content(path.join(dirpath, fle), [lines])

    return

# _____             ________________________________________________
# ____/ MAIN CALL  /_______________________________________________/
#

__author__ = "Sebastien E. Bourban; Noemie Durand"
__date__ = "$19-Jul-2010 08:51:29$"


def main():
    """
        Main function of doxygenTELEMAC
    """
    bypass = False  # /!\ Temporary bypass for subroutine within programs

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Reads config file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\n\nLoading Options and Configurations\n'+'~'*72+'\n')
    parser = ArgumentParser(\
        formatter_class=RawDescriptionHelpFormatter,
        description=('''\n
Generate the DOXYGEN documentation of the whole TELEMAC system.
        '''),
        usage=' (--help for help)\n---------\n       =>  '\
                '%(prog)s [options] \n---------')
    parser = add_config_argument(parser)
    parser.add_argument(\
        "-d", "--doxydir",
        dest="doxyDir", default='',
        help="specify the root, default is taken from config file")
    parser.add_argument(\
        "-m", "--modules",
        dest="modules", default='',
        help="specify the list modules, default is taken from config file")
    options = parser.parse_args()


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Environment ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    update_config(options)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ banners ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    svn_banner(CFGS.get_root())

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Works for one configuration only ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Works for only one configuration ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    cfg = CFGS.configs[CFGS.cfgname]

    # still in lower case
    if options.modules != '':
        cfg['modules'] = options.modules.replace(',', ' ')\
                                        .replace(';', ' ')\
                                        .replace('.', ' ')
    if options.doxyDir == '':
        cfg.update({'doxydocs':path.join(cfg['root'],
                                         'documentation',
                                         CFGS.cfgname)})
    else:
        cfg.update({'doxydocs':options.doxyDir})
    if not path.isdir(cfg['doxydocs']):
        create_directories(cfg['doxydocs'])
    # parsing for proper naming
    CFGS.compute_doxy_info()
    print('\n\nScanning the source code for:\n'+'~'*72+'\n')
    CFGS.light_dump()

    # ~~ Scans all source files to build a relation database ~~
    fic, _, _, _, _, _, _, racine = scan_sources(CFGS.cfgname, cfg, bypass)

    # ~~ Scann all source files to update Doxygen ~~~~~~~~~~~~~~~~
    for mod in fic:
        print('\nCreating the DOXYGEN headers for ' + mod + '\n'+'~'*72+'\n')
        for ifile in fic[mod]:

            # ~~ Read the content of the source file ~~~~~~~~~~~~
            ilines = get_file_content(ifile)
            # ~~ Update its Doxygen content ~~~~~~~~~~~~~~~~~~~~~
            olines = create_doxygen(ifile, ilines, mod, racine)
            # ~~ Make sure the distination exists ~~~~~~~~~~~~~~~
            ofile = ifile.replace(cfg['root'], cfg['doxydocs'])
            create_directories(path.dirname(ofile))
            # ~~ Write the content of the source file ~~~~~~~~~~~
            put_file_content(ofile, olines)

    # ~~ Run Doxygen ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\nNow running DOXYGEN within ' + cfg['doxydocs'] + '\n'+'~'*72+'\n')
    chdir(cfg['doxydocs'])
    if not path.exists(cfg['cmd_doxygen']):
        raise Exception('Do not know where to find {}\n '
                        '... you can correct this through the key '
                        'cmd_doxygen in your configuration file'
                        ''.format(cfg['cmd_doxygen']))
    if sp.call([cfg['cmd_doxygen']]):
        raise Exception

    # ~~ Scan all HTML files and replace template in phases
    replace_doxygen(path.join(cfg['doxydocs'], 'html'))


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# ~~~~ Jenkins' success message ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('\n\nMy work is done\n\n')

    sys.exit(0)

if __name__ == "__main__":
    main()
