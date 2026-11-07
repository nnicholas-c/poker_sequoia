"""Kevin 1: Bay Area poker, adaptive table-local policy.

Offline flop-only preflop estimates are embedded; no network, subprocess, file writes,
background work, or table state outside the returned memory. See kevin/REVIEW.md.
"""
import base64
import itertools
import random
import struct
import zlib
from time import perf_counter_ns

import eval7
from poker_agent_sdk import Agent as BaseAgent, Action, icm

NAMES = tuple(r + s for r in '23456789TJQKA' for s in 'cdhs')
CARDS = tuple(eval7.Card(c) for c in NAMES)
INDEX = {c: i for i, c in enumerate(NAMES)}
PAIRS = ((0, 1), (0, 2), (1, 2))
EVAL = eval7.evaluate
BUDGET_NS = 450_000

# 1,755 suit-isomorphic classes expanded to 22,100 physical triples.
# Each row: equity vs random, equity vs tight, combination percentile.
_PREFLOP_BYTES = zlib.decompress(base64.b85decode(
    'c-oYmcequ>_4g0GNmEpUy<smXiiNwz9yN&(<FQ14MvXPG#9l#TV$>Loi8T~ans6`Dd%Kt3d+)vXA|fEZcOT~LS?j**%Pjs|&wkF?'
    'duFY@r>yU1W^TXphDO=!H?())hxFpy7S3i5rpp$#qgmx&7Ir2xf-V^PPdej+XW@0rZw~*SbLgaZCer19$d<8(P;dH<*539~8C$>S'
    ';g=ab%TfkQnG5NI+5e$CK4=chW2uX+%$D+7uJbY<Zr%BRxxIky{o`a>{M>JZoy|_B;@?l86Q@1|ugl+bqr2bfNGET9qx5=vy7+-l'
    'X=(2khp;D8QJvBLK0RrDr9xWN<MrIP@O8g7>35O0Gnrj<)T-6gZGNpX|K-2e@5BFFR5*oher6aot^eR5?xWum-G|$U>qG2YUKdL_'
    'gKsUdkpATNiN{6O*K!}-pXfd^Mzg8qipg|o|2u_URJe$$3?4!s%)g<Gy@D40G=<LJaHX&_nKks)k!$D|Yc3WxiiPc+=f6Sk@Zr5<'
    '==ahmD5iScxo>g2;_m={=lMPL7~$CIF~ZmNd!qZJd*XLv1#KNXk6vru6vo~1&e-0K!~0&)@8!F3c<&gBsih6)?;Co@Ebj(>PvYON'
    'jA{IR<JWEP8^0dj4NLjavuy8Vc$R!8=h9W%S5mnV&4gW4IE}hA?L|*^zaL)bb|&*VUGvr7X;0TTOYI(1@9K_piF@M^_7JMju|sZ*'
    'k<E^!x^;)rl@0$~de5(ERR4FV`8jV2JCoT)d!AiFz5d%k{Fna*-G~3TsBk|$@_)PNto3^c-3Q$h-ACGEX!onV=*)S^??=&>mky?l'
    'H#`IFY<4`ocW*E1)$#FCyDvRC>LYr1&Z~#8C(=(3bfHeaeWbJuBgm~BPAwn$OQ}78&ite+{o&kK%Gmwr{MQR<O0QQ-?auV@HEpQT'
    '7tKrW(~*`P+md#aYa#4RW;gXZV<X+Qty-C9@q41@hG+46qUZ8w6%}rw|LZxC&N$(uLp&FiL4PhP1A4A3!{L1k_&R@o;_sXMMl9bH'
    'e<%5UEZ-OZ7UK88-x|6P|1LtjZ1D~8vc#8vQ<iT~epB&pP`)#voR;rVzK8Mek-vww=jz`DdM^4d@N?xivY=PV|7T~j+iB0cgXs1<'
    'k1k_xrR^sVr~S=O5O(sO{OXBOzC90iHoKg9{c8rjJi9>HMTM*A_L0SOZ;MOI*!nkU>9geTQQvX6eFXYF|3=WajJ|i?_vzoM?c3M;'
    'EO}4#4x{%Cy~F5zL+`47fBdeZ`}22L|MpS)fcsp%ec;~+`c5rv1@5!-wgUB8WxrYN+r;0j{%zvx`nQR%>t#UYL1jSYL1jSY$z<ly'
    'qWWE_Nk!Z~SlSj#8*=#lDf&JCeh;@TLf^h+tj^mdy)Ck|A^2N}k4xpZ5Fd;3`&-7M^8Wn$ijP0hvn*{F{+8o&2i}g^<_@79Lv5F('
    '4Z-b+rGMw&a=d?+-*UVi<JWENSh#L$$HH~qhFJWA%4TWnZ2r;9CfmAMRHI)9di$2U%h)66!qPGy{EpCdZnvh6&wfPjG*8-}KGf@f'
    '9cb^5uR=SM`I36>YDEvdpZtCZjs1HodieDhORsmPg6dz;*g?&Ooy{(#Q?^W?yH;H-{>y)Z?!*6ERJeg|_+U9b{P>yhKIoq4KGGgR'
    'Q!eY9^GPN%fmZyzm|hz27__t5w)E&9KB6wqCS@2#wIBW;)!h67w6ocP^wPYR)TZR+T>EqEM}vI((}Di7>1#Ui<`!k_9@Kev7kX}1'
    'l9%gGv!4En`VD*~*Pa*bYn8U`!Cpi|YYwEjPyVvZv-myHbHlUvJ@Iq-v$oTNAD8&=1w9v)L4PhT1A1<-Gno?F)NBA<wdncW@2UT!'
    '-0!iyfMy>#&F5zO(3)Otso8t4K|2{Ie0J?5KOY%J^E&*8&id#DXlJv%>E)OIL(Qiq{~b>Mp4FZ1Ipew9`?jrTuk?Ei_9EK#W{J-q'
    'PM}tOhEStd9?jjSq}Mn8KEY13yq7i>=Cr)zxkr`%%0G8F)&5~z?pfR}D$KaqEe_B}cdjB{HeLo?&QLa922@U7HdzL}oV;wAOci&_'
    'V=HOf#;&lOxXgMvQJGOWQJGOWxqbL;GP=&&MoYWL+wFMUF572*&v-k}+fU1VQ2UJTBirZDZdlqG-fmdh8Q!+r`U2jzTl#{~cFA(a'
    '`vqQ3OTQr7L(6mZ_8C1Fwa@6evaJr^spY%o->L1p4&SNeyOw={rSIVVLcH&geSxL#2yKgO-{Sp<^n;}z;eLqsBeH#qmlL(msGPV@'
    '(aVY2XH-tvR#$L0A2XAFe0q8rdpG_0gaPRsDsLAR9^uMwtKdF<r3G<2o2}#?ePbQ%zkR5%GnpgY_t#CPF~i>$c2QvsSM=pf`l0vV'
    '%h=^y{Us%I*^vu{oy}Hv9qX;3{^$K$*tqYojQRO*&=~&k#@M)>=WRHeU+Dc5?+bAM67RFnm|yladfSWIN!0eDb`rI*=>DjU#qBU}'
    'd-XmG_iJd*g8H@4wxj;V(#N5`81->@%+LE8+&1ccjovomb_unOs9nNspx#dEZ6NOZP#dV1N49~ek3;<+njh)?Af6MUevtPmdjDeS'
    '6Y<yp^@(U~p!bP*%+LE8)TijzQJ;dYqdo=qHF}?duH!Q6<ws@4_0r3X%8$y7`^wF9^9uv%zCouRq93&Mp_ab#@a8+X&*C|*!|QW#'
    'UMrr{<NYt{b1i)(YV$4mE8gZ?a#sBQmYkLBQ$pWi$y1?cS^8+)XT@`jvcI<E7<qrK_tBQV68D?&e3Wcs<M}Ar#>R6{vdxd@pk%)p'
    '&q49>$hJM6cS2>e_381v6DpgnPe=WGJm<;#cU#Vr_wT4rxAc{IA7q(-@!weHU-CDW`B(UjrGMwwE&aRfL*xBBzi#Q@<@L~4TKtdd'
    'Vi^Ni{EzBl8v}&8$a*cJfAk)nehYa!VVjq?9_)E_{kr^33EezvXztrdzSC=K4@tjS%})B+Ge2qV=d*)pYPTV|H9<v%pVD2Yy+yMI'
    'yeaI20dCr6sAqt~fBA3FefWQqx->j6#Mec?54tD1kG$s`s`2q)y0i1|O8+~Q&T8I{E^qweA?%5C&CWuvtxu*^qrOR*dCgAR*j|@)'
    '^KEQ*>eT2f`o2rjk9VbZE85df`=y=9%%avEd(rRiy(h;`Y`UqpXE6HE*pu3%W1hU7$!wy|7Yw7}H=ZG$#qWup%b&&XiJr@!mCb%%'
    'de3FF^e;!i=b|#8=b|#8=gKn7qRM|9>BqN|sL|=A-_f`~9>VTL!<v6Vv;Ob(+<(jU9FmTcH9M1;MpYm0NwZe|Ay?nqFK(6gp_-k^'
    'Orjl)y3=omKU`YQ>GW*v?sQ+Z`*V!MQ|}h%7zu7C@72x|JNx&ln5ymVL64sHLhir6=sYU-Uulo0&BwILu@eaw^yfaEJR>xQRvg(o'
    'y??MPxK1r+Q2*B_5HFi7gI-QqHeLo)PF^-%22@U7w*54^<z(7?=YCjDRAyXGRAy98RAy98Zcm`+t{9PyftL<1I;34xIEZG?=|Z19'
    '^>XgJIQr~ix$gqoBWO`!@7$WrqQZIftNo*??*+FV!Y-km7Y?R{d!NfacjWgy(lTgv($-b@y0vfX#?z9Ahk4F$cB$V=(sdtsJ83`9'
    '-rX+OekSeeIqw(wcD0aRd+x7v_Vvxn*pp~OznQsjFj@EU+KnsydXouMuWLU)o(y&-GmbibKaf^_@uwVXH23koo;4amg`4wvQEngQ'
    'W^X(|Uw(TU$-40J>-FMw;bq443U!fX*6YRV!pn^773z|VC2H^7=EoAKUV0r-y>K1%dZ9X^df__i^^*4Cjcw3%ImWPzAHtZ&GDec)'
    '9DdLEcu9^);`hPh9Q{80x*P*o`fJ|*TKelSMzW2m_;@Kkrjp|vUS`YqijQI9<10R{usj!!we;traSnQ}9P@<!&elKj{x04>^8U`&'
    'Kk_k^Wemp0SC%mtA5&SzV4;uZez1(kq)+1GG42P;c#Mw|Eak-G98^wyoP*1$k8@Bt`E}Wc#``1LzgYSs-iKQHqtL(D`Xf0Wi;vmD'
    '7|b$e<6|((n2nFYEMqn~&fz|fkKd%vE#o)tbIbUR`#C;-<Ndy^UTB=7*9(tx^m^g3oL(<9&O!B(<D5$Fu0IVW+E^^?B-d2?hk2CG'
    'I|aL@8*}+y8hz`N!p>x>y7oV=qt3tSAnc;Ty6)Om>!`(ZmkK+Rso_Qq*hwque^AD*;@%!NCe6nN`(!uw@y+zFR$mlI`zUwUoHg`H'
    '-E)cCMTHgJC2x(VF@GLW#@5GdwwzV?4bDLwUXBR;UXGp6*iRoH$}t!k*Tu(*C}+j*iN`!>e1dX2XpD!(HfRiqayV%G!^bxISP_pW'
    'QT|OIPx3Jp9@kmMmM9mek1bKoN{;dLF$o?Ipxlc-9zbJ~LyhsYvB#mtCwh(rl}8_Ypz_Eu2_9SO<4-iUMB`7C(?jD=K9<wRb(XOx'
    '&ROYWQ8Xq;V^Nf|;$_A;AHDy@V+Pd!qA>&Nf6<sh?|*TgM=w7f8=x^N8XKT7DjFN0@dF<l;QXOJUPWV3eY}dtqWX9hk45$IDj)OU'
    'ab0}uigSr*?5fWZ@Yog25%jSu%2~-Vo<5etV?2E<hp+2nIXuQgV>xtPAIsq}o?b`n2fdDXOsm%s*B8}MuP>@2uJ2wdc)b^0a$`9-'
    'UbT#MZDZQQ%Lk(0OWpJE#>QwYYSE7QI2nzNZDU$AHnZrYeEb>LM&<a{qK)#gAJ--0dMJ99Wh{-xmKH5rj;rHZHXm1`v9x7Oi^oD1'
    '-7}1ZEV^ge@nlTvEIT%fYn{A2ajlb=M~=bb`X(-0eC%z}H&NMaV{bGLk8A649B$Fp`8XVny)9!}ee7Y=G5Oddu4BrvM_k9`V-JgV'
    '$;)rkF8TO2u3gIUZCtyQV<)a%#`Q{67u#4pu2-VESjOsDuZ(N`a@-!*`uVusqV@A}yG85g<90Mww~T4=_|}r2<YT{hep3F%lAq+i'
    'iRUNfZ{p*2Io7p|+xhkQxLsbijN8L?%eY-$=VRJ<d{NzPWBYh~aoyu%drN$A-GiOUtfK$kKamy|H7R3{qhAf`=Gz2xJ=jHsqv$`a'
    'KcfSmJe}*KTkY%R`)J)xzWs^!4#<7`33uJ~xVE0b9!QTD7y9)G++Iv4?e0faE8bA%zx+4oKH<OF>_U2=!D#A!)-8v)54xv*A8se@'
    '&-kLReETzs?w`{k=M!WnZCa%RU3{B1gYG=Fn64UnAGDMC%YySJ`n~Im>7Q@3_rC2<pWofaufOB=SenzW*pKH2QSse{zP=Ob{i7!M'
    'oLjIH)_p^d?w)n$&*Jw)&kfI#_tc-upOuVx{(IcO+?WSH7nMPOE-C|huC&L{s<YcuwSPaAo8NtYYcD^)L-q)|XHPeO*1&oiKWZU0'
    'o_;p86Au6NA3yZ#1y)hHqf63nP`9Vh(YKAK4UG@ZS>_Fx;rZK1^kH#vIz|ol6nbOmSU)!(K{u~%>+@YhXz2T$((ypvPVTwpo^Sm;'
    'Xgn?L(#Ov!O6Y;Y4}BjR>}<B0`){?`^xfJoiI<I+0hcqBjh6wHlb21FK`*B)TLss;$t=&q>*d5{*2{^?jLM11jLXUGCG_g@VruxC'
    '>vEiY=i|qv%)DkNYd~JwKEdx>K9l<YUvC<@;`h)_+M+JEeU-LFTl#lR&(6^7WK8?u$$flod=@P(nv#y|bbAP`Km7}Tw#5`0w57NA'
    '|1^4|R^N2rzhJMT+U@71du`o*;zYmK)^K{h(YI;tC2uF|s;<8Mo7}ppqQWIqq1hyQX7M$-w&K%{Ez@=*Zx<DAqZi*FL>)e@UurL)'
    'QI!W%h1$Q)wXqc+>z}r_!LI5?|7VHs_d{KHnQ^^%U3mHRdhxo*GVAr?b>U^k^$K-K#vZE*_xrJjUN2lnR4=`bs9va!s9v~^dcCB*'
    'hNhNGpgsR<l>1)xT~LyKJDQz5t6sOR{<+g=P;rm6kI?L7@3?A1=J<W&X45~bcTMMjnw`mPp<_-SOZPu?N^b7<n=OOWz2Y@H$$?yQ'
    '{x?2PvVdB>7|tos?4rUMw7AMQROPh$a@VJi9Om1ErKNrA;B>8M-cI(ezv#<_e((BKRCB?YT)&gVy6s0L={|UQJ88#$_uMF-OIbii'
    'we9DhJBJ<{+{@2ZgPp8V8s2WcU!ydKHh<C1uX!I!cbz)K_uaux{4@L?Lv#K~##bE<eC@|tb7}0I-P655gMFmy)NV8V=8Ox8*PYi9'
    '`GMD+*Ae-F*Im|8_XDrHtfTG+S$AGX<cCoAY__U9?utot;}c&)KOmnVKOmnVKOmnVKOmoAKOmpze&F`u&vEqYd|qIiNAS6iWv;~M'
    '8sR>+c@v+TSnh-7JLo?AIv<C}$L(@1U>Udbxl(*?CFf1?xs{yn@G@KGS-i~gc^02v*q)2#JNk3cd<Q*O&bh+4*D_9)WA*qrS&n<-'
    '<77FviqFOP+{!W+<8v#^T#S#^r5`NwGVT-0yo}Em;`1^-U$B%D&v*24;yIdLPBh;^<t#f#%a1cH<5E7(w2VvnIMX&R4dYD9xKz%?'
    'EOWOo7qiUW_*~33cMEed+uV(hrTO?jK97@rw#?&#pDpt^IsT8&<K!GCUN1D?!SzCOI=x<KzJuz8<~z7v{5l`kS;m2UtZNwuhH;&3'
    '9LUFY@o^v@*V)E_VeV#`>&base6A<waq+pHoX1(_dSUKnnd`~1E}zT9=Y2A!mU&-@qh;PF$McqXUx=e^-p9xGaX;Ysj_wCM2h{z5'
    '<~zs_cn*mCfaW{M4}88;(+z%c8C~${Yr@WE8@N^vZJ}FkpH?94`tF15M!Mwvox;v!8o1@J?WSF?&MRXd>8`D{gt}L|grr@|Jz8-K'
    'b!+#Cu(R13Ztjky^zbL|3cIMVw!3Wo82X^`EyB)Zj&)m)olVP!RxV>VaC5q>OUskDiwb|?PI#b#tKM*_u#@q|A1<Dl8*gwM&-LP('
    '7yk{Kiyf}UgnuvRT)L))=9PTzrq2g$b4*?HlJ`V&C4F9lH7PVVL~|lEZ$dhhet$VvLUT-g9*XrleICl^Vt77inUm^sXEY~8nwKnt'
    'K9@oB2t1e3=Mh-DL32ZW&VuKvXwHJ>sz{^J%OmG3NE6iOt$0qV&s)))6wO=t+zQPHZF5+CE|2H1Nb}O?ut@VNt1W7C4K!{?a}6|Z'
    '$8!xdZbx$sG;Y`D6uA8QoC41~(40aqKb}*d@`pJE)*R717tLYyc`lm6;(4w<hsE<;uI1_TLCc&M=N8bMSI;e=IWN|{^f@omykvdR'
    'TmX%e(OdwHlhIrNjgyh~f#!z#TmX-g(U@PaFCO!wxiA{@>-EJN2db|==EwEra{+zMi{`~x-_+;DSl`s=#dyw(=EZ2vtIvz&+((}e'
    'TIR?o*MaBAdaeV_k+J55=E!=k1J99l&5Qd4%>nV;P@e<hxgnYZ>eta65M9S}K>a$J1LC=%?i1`c-6z;T$S1mgkWa9GkWX~~AfI6W'
    'lwMohxAc9UOn6>wnN!E-&WEp8qTlnm>fz48(VW-9xbpcpnuA;B&iWkC!gI=bu7%;`bIdry$?q@qL<_g6Kg%*_$8%T<a~tOG7Uq`E'
    '-_e}iGIvIEE(@Q@=Ug^Elh0e@Os1Si$C*qykG3$Gp*(!9XW=kW*=%!s3x}zf%{Ir^=ld20n9uhu3^1SXqdC51?u_O*7T%K2aV)&0'
    'oa4lKOF74hGnTUaamG^4(c+9HFTaJcl;!91vN%_X>te|X#JNgT7fVh6%`t6EGS3ghnPi?HurSFoKM-e<Wqv@<30UUNcuo=LC*_<X'
    '&QHoYg@vEw^U63sDd!XxW-`>*!c59}bex&w^|djRyuNW}Qr4Hxl`Nd3UUyp#A<jvny4!LHaZVD~J)T2A`2-6i&GQKsMw;gnER3|w'
    'C&U?Po=?Czg!tSU&!gk|sr*e`Kjpu%=%@TQ7X6g}#-g9f-^B9?a!wu3C&=sZd;-62$tOtv#PbRKx+R|=uZOv_<^4gvvgI7&?+@~o'
    'CFfvye~_<iIS1~mU?=Or>-8O&t_{!I$rz*N9iwt%40K)oW*U|JbAlg(b)fDQThh%Rw}5uCpUI&6+xqhz`q1qozVT=0ji6nReUt9t'
    'khha|sb04}e(gs1ul$XEANk*{RH4mUpHtQEgYJp%!|n0(;O{^8^R-d*?nR%b^JUFW`owonndJM&m9+Hp*>uELS3o<Nqt&h3)6duD'
    '(40L(eSg=BcJ^sSJ)d}8*h!o0uITG?ytC+)lc)H-0>)6|pTAA__sHAXY{or$@mAV*>008?;`c<)<<H{xM9<~VO6GC*-Z$B=<<y^x'
    '%7C7W%7C6L%dmvr|959U&R;+!mrqLjJKZj!&o2J2*P|!X?2SFr{ctop8S|7(ZRy9iV`$~MgS@V-+er@R<(Iqoe9lO!(5V&8`{9|~'
    '^|zO|N%K6xUP-H4P0778NjXpYa)}>nO`xg|7N+}M<n3gynC*A>@O#B9rdDg)<#K4r7~|o+VP2EBb3Poo&ijy;jh6wHGn7r1K`$pS'
    'n=FG~PF}WTE&o$(*XGvp<8q=h>*YjcM&(3hM&;yoa{p@kx_h5Yp*z3*CfzGcx0lgpmAX>1D_pMKe&(l=v~Aby<o=Cc8t%t$JISqI'
    'NWZ_eF0_;HZcm>Q|LxD9CZh+Wb=2&nz8xBuq%j(IRZl-Jo<hGruP`ltu*Xru;@-4-^%J@L)oXVQ_4%vuRCxWjehkm;tyJ@&VSY@z'
    'jQ+5skhXSrxibe>y*fEPe=u(s6|STG<3`ghr=C~(`*pN>%}n}W&;_~qa<>KT)46lr&SWaPVUJFxQ$Oubye_=VxL%<yyv(>>p)S14'
    's9wA-vdntDcwLhD_!;L<$<4=6y>K1%df__i^+I(-^+I(-^^*1+n$o$%&+kgdXr<TkV;IdYD%?#as~6A@wW{UjP@66voX)2-JNc$6'
    'ZXW5ssa;g@;vcBn{94dX_FkLz#7w{U+H%_e^f;ee)9qv~T>sU+J~uU$zO2xh7G3thA?%6NDAUC=coV2~y{~<KehD>OJS?qmu=mi@'
    '@6V+1qbeQTH|($Nd|xn^8okvno&N@VCOz`&UVhE{3cB{ap+5IAhZ-Fi<oz7%Y<509zh*EU7<OxJtoZ$!Z__p1#do(#=lj9lM1Om9'
    'F>Sr{^xWP}uPh$q_ih?TPd4n}+lOFhv&XyQyMLnnKMW|4b?0?Neh78vb;N!Mb?0?NevozNbwqv$b?0?Ne&BV_Wa_v--LizP-+lvO'
    'KOmpze!xD_{eXOe{eXO;`vLg``9b<*G0p2T%=f=5OUGmF(lNGXC;8i=n<x7G?HnrKuVb2P((Ghk%J;wO>G!3aTl$TEo%&F-le#b8'
    'G0K0}OR3HHUTLmOvy*2Hf1-zf)&}}#zd@8~a`qwYRdjU8NS`;`K>x^2NzY2w?K$+?lp(%e>!`xdgMD8)iuyg%!S8Rz?M-yoO}+hI'
    'j-_Mf_d5Iba~4f}{>yalzPz2ZnGIj;>f6i}G;iFuX&$fs_>jlT+u7_sdij$<w5RLOl=K%f`;7K|$4Yvx{=hU|!Cp_}xApX6_&qeF'
    '?Et!`pki+BcHJv|(;Qc@*U@8N_VxWpX`BB@KJT}d+FaI=rtZD4jD4c}@rH7)`rP&f+*jNu*l)pC+$YFy(pTI+y5FR)xKEJZg0Hww'
    'u-}5OxKFU(xUY_KpFZ%D-y=@<8}^~@H{?U?H{FNWZ^(zb->?sLzhNIDzj6EUay2-I6Y?9jd`QUQ*m6E0XTtAe$^Y=Yise2iZ-ef`'
    'uk(C@CI2Av3Gw`c%=yG~L^A(l$q|K|hRl=1^F=Zz6VDgPoJst-C~t$Fi}N=6bLDlJbBN9N`TX57-<LUu_<Wz|h%7lJo+Gm4lz5KF'
    'l2a<1x8XjC<(H%%;`t@%hj@NT=4veE)blo|oH%czmlNe}P&sAZCd`*D^J_j|w#=_(PQWt14)bNp{F>*KY&j^NUyA3TcuvWZgW@?Q'
    'TMjDZ1h}6q`6!vku;in-&n@{V?&o+uO6D=*^+I_YR4<&j(d&hCQ+mB{-bSyNydLJKw)t$BpIYX#a(-%=&xZM_Wj-tC?3Vc~&qu{`'
    'Rx$?_&sp&tlqF{+^HG+ZRmefva#noK9^z=pU&*{gJbxu~GV%NskE1Pr#bX-JU&*|L#SePk2KfQyZIB;O-Uj;t<!y97pu7$CL%7c8'
    'gO>RtpATB*k8(a3pFhg^V0`|_=Yy8{BcBgi=8rOe70+?W{8c>1#dB7+92d`7#dBOdXJyH8@tl<<$HnK=GS3jtcgZ}1CEvy0lX$*M'
    'zBBQB7k^JI`7W7fi08X_p26Zbl(#{C!?`cyH<Y(Qe$(?d$ZsfbgZzf_Hpp-C`Y~=t@dA2eOATRXGAFuS*Zxe8)#+3q?GxM+AMT}3'
    'AMY*fqQVp0;66L)xktMQJCixh{q?TO?z4B^7j`y#f-86S3Ti&2tFVg-PjOrS{5}2W<B!YOr@LRhwwoTl{BOce{`=&6+td5x?V`ft'
    '-SXx?QQKktgq`fY|H>ofTz((^yq(R~c9-p$NDT(xPSQTkeZF&JX}>VGfZIidN4vEX*3*d()*)`A9G8t*;=e&TsKaA~(C=jqO3#(y'
    'd|Jp^p*)x+w}zM{c~6uhLOC&%BSQHclnX-nB9sf#?=Kl1lv~sDZ#cJx@^3r`rRTvcxj4*X>A5(>EXnd<Mo7z_pd1d$pI}A^<xemd'
    'q?HHdYH&UWaY1@{$}%=uE)M1Ea4t^I*P&b-%Gb%<7tVvla(6g~spsx+4pYzFA!dn}8Ru9~PE60SpnL_+v7mf~o?}7z3Y<&P%a3v?'
    'IH!klDJZ9>=TdOKCFD|2?hfbo5I?5p_i*k`&+nn!9nSCZ9Fd*}v*h|PvxIVedQKJR`cO_)&-GzuiPsn9Ku~@F<v{fO0A^QEen8KG'
    'p!@)4cu;--<vR5G;#>#Hhag4;)mP7T;Cu+;c2IpeuY&kAJs*gfG(8`Pa(yTth;w}?AE@X0a6XW;TY4VMk{iU#lAasHteT!1L^)oZ'
    '8`N{WC^v|irQj2sqd++^Jx76aVkk$U&&M%aqR+>1jsoSx^c)4AkE2`!%2(*Q2<#t}i$MNC42kX^oQu%?gK`nbKQb4A_%}U&i1{}?'
    'e~5B}IDd$kH$8udbAx*R5ak9@{*dQzP#(;ZOT^3)$|a(lvz|-D%#xl<L^)@aOT^5Qo=Zf`lJuvZ`@%UfJ@<vL>$xv<9p}FE>nQhy'
    'uA|%+&WY){FLWLG5cw1N5cw1N5c?DP5cyg6A@;NGL*!57L+s}ouJ$jw`n8#Q{?L+pwB#5MmuEx2mpt3y<tlM*Fus;k<}LMHr6tFR'
    '^Np5ui#%5rU#lo{ahA1;;r=}5W?7$zo@L2x;`ND^wWT4?X<1t;^PGBa)0$({a#NOdh&(rCS%)ZdQ<k-dp*)tghcZ_dUwg>QQ+DlP'
    'e7&JwHcKwlvfdDt&5{d6c~Q$+SDqKOtaasiQJf2n=NNImF}|*l=YlNj3S}-RzOInxf-GwZdHF4C31z-9zLrqt8{=yUWiCtR7-Q=P'
    'QC)1g)A;&9R2NI`6y@S9Yj0&9HNN(i=TR+dZ+RZovi4TyQT5!ZCC7+!FY$GPJojQ-C&+Uz@pXbc_hMNmD046IwSm08mbHO0*JN26'
    '$m<(l8z^&4@wI`nzB0!cTMvlpZppRU)&rutTXL=O^?<nUmRzfzceSkr4tZD0T40`cwX6k}dDr+_V3~K-bFG#fBhEL**Zs+Snq}Qz'
    '$aUD({e@hIW!<05r^VO($y`T#t)I*V#n<{t|5(=gasOD>`UU@3*7|Y(Sl0S+|L~lTWqlv=l`S`GS>K0z70=CD*7qS_S#q;DR~BEJ'
    '%=5ICwaGkBYgwBt^R$+=$stc`S)0uBw3fBWJWq>qvz8nq&No{4I-V<w^L6|;7QT-E#=_U}-&puM`I|Uj$A4qV)AH-KJZ-pc$<s=I'
    '#`CoDdOS}nbC2;nEx&Hb)5_c<&oRc|Pvl!mF4yvYV&7VFx$*ZC`PP!lwY;Cmx6;ou=%u&9p5(!vL+=e9@5ig?y0nj4HQ0}7OX!)6'
    'U!{9uBm1^bKK6TMkEF$82jy};$=?3gE*g^V^B?R3w0-YfdiB|z#Q)2GgYOgmoAg<aH=geMEd4(Cp89>{J*Ux#(+2q5?;?8i(J@}j'
    '*6n1^?VH{i;`iL1Of9E&P4h*XT~s)Le%JIP`op=e<nmz2-t`CbU}NaUb^X%ZQQl5|^T!*%@p-dp^yyIp(>c^t4-QV}7kNAB<4zbk'
    'GS|oPXO+FD_FVZaet-SB@>vIH$CTYvSamz0=b|#;=jvs^&*k<K`pb2#b2+^v_cExYd%B0bW+(HDcb`8vzevVr`wEKEd6Q-*W4X`n'
    '9N@=wi)dbl;psmAx;=&dbHS)IuhO_#f1g(wL)YH)RhmB!_A+|C-&oJ2&7q3f5q_LJld4qtHqHO!?c^P9{=#TK)?G}`yGcGDHJgrJ'
    '(Jh_R<?Uq8&!**8_%lR8*?1XnIYZfa8BjT8*?4*Ma>}x8qs^yI^Lvcz<-}#y%ZbX2%c++cmowPOKIAiw|J<M1x0Ie+^<6s7)a}Kz'
    'zei7h|5dbP@z8Xif6Y$D<o|B5*0T`nsO^wqKL<hfJZiSIozK^;qYsz$Nq?i;)9A{bZT)vQkFLD5Gc~E$ESJ-6SUkz^aUJX=f3p9M'
    'J}Fz<ZBRcyo?k@g*6omf7r~xFH+CB8zl&}3?c!n7>%R?hZF|AHp|8o?Nf}1<>y;}*;)mt04fB2&Pp{tHG0nRMyMep!t*S2BJD1l*'
    'mRYYCuM00Tu2-mwEVEuOUKd_wT(3}<WH0VhPo0t5iyPGo)e+ST*HNz*sw1iwuA^QrZYO<i+s$2k|2vAF`0%TA4zAhBKI9WCOz?Y>'
    'ucoD4Mp1`ajiH^)<6ilGqMyg@r51Ngr%P@ucS!qRXN>jsB3k(EsMLp=oyqK=wO93|$|H{|y}pZHxpo4b*0bgz>@Bo&L^nF)gp+c<'
    'dhUus@2i>g%<j;R<?UoHy!P?_{=A7fRCMpReq6VU{y42?nxhN$Dk^uNoo`Qe(93%#`m!yd&NU|aev{jK=$;)*e12dq{rSyaetx}?'
    'HoQ2Bp7~=#VJCID=(_p2x+M9HTWd_s<u{U?=f%gg&gDF%eS&LNRK*>fzl6H;IwC*Fy7M|BKZLsTI$}TYy7T(#e&BWIb;N$)bwAoQ'
    'ziyMC7wCRKKEZxKKGFSveS-X;`vmy``vm!c+jD5{wy%ATWet6ON&npW0?1CzHF&CRcYnUaa_YFQOPYVy?4%uA^W6mBR_~y{p4W?-'
    'Ryyhs_7Zw(We2Yv|44&(@1(1*uW$%^AKkEMvd_isqNdFjr7_a%#GkXC{>r~&Khq^A4W=e7HW9YxQ|IG5r@npjj-lSStLe{m`lRh%'
    '-cH`Jh98X1y<^F^WkG}9xp7N!pCN-=rSS^(db<9{;XXIW^Nn-qkvGG+62bnNhMhPqSGHt4HmK4NKOXymuDPi%eY~KGu#+;MIcT6S'
    'a|Ks)^G3g~`x1KX`8MhMnYWYJy}4?NkKH=DY56d(?M|hiKKNUz9pvp~&-ts%?eu%j2VZfYAir^6ai3tnabIztAio7)ai1W+abHQF'
    '=zinAl0MP>#(h;(c${ldQqKKQzN7&84fzoH4f_!J4f#;_8}cFY8}cFY8}cFYoAlvQnsMfEpJ!e{e|uqs*F=!Lhu-{ra<1)7bin0>'
    'UHzI1-A<T+H=pY5nSp)OY~l>h&FXe?mRZf#%l%nq+h|Lbd44RX+u3YoSFh_F+P%G3t{wZP+2FM8((I%!cx%}T-xo}!_p+^0A8K}@'
    'y<X9vzt`FK(qC$iNylBfy@*yHTja;CTd7L<?w(!QM#GO8l9oSj7ZsLwuiP=8#?75c$#}I|?;<~5T~6&kYM1s4c{_R5=`$zho|Vb$'
    'rSm@?Ok;+Z&%N_+9@{H@|MPYduMN+SN_peHzv}IElLK_r#{+#1irX9Ljgtm?P2m8Ye)KY*D_cMtkL&4KbZ(b(H*^_GmmRsV^uHN*'
    ')+c-EZ~fL&($`#b%7nDv$=k`CZtG{A{hV$G9sQdzx&A8|S66M(Bh70C`y^NR(oSmk%dZN!Z@CYVpSf?j50Rg_Z@CYVpSf?j53!$v'
    'Z@CY#pM!6?50Rg_Z@CY#pSf?(cHdrF&D~Y+5$I>+bL3~_bL3~_bL402bKTF_=enPf&yk<8&yk;lefT+Z{W{MxTk_I8mu|_u%iOiR'
    'PdpFLbKUX#;QTqd56_?Tysjk=%yY}}Jh05Y$8+^E_a4vH^W3s5XFP8&%WTQphkUi=xj280o{Mt$`g7%Vo=1)6U3nhWl6RGP)Og-i'
    '=I!ITeV(hg<o0E*KAzi`xnJ&wc%EP8pDlTQo*R$n`DOk&UQU!hN9Dvhe^gFAe~!z^uk+k&JkQDVmX<uH%*|TzoFQ*%$#e4DzC{a='
    'x&62nz;pXnEg<Cf<63~spL3sEbOG*Xi!Q)@9@hnAKG~uR@Z55|URWd0>xJ{@dc9Eo9Mucw&-HrA{5j7PTJnk^PiV_4hCHDquPF0`'
    '@w_6>6Wa2MTo;II2T~V^YX@8luxSTe7qDmtK?|^G2RwHwbK`LxfydFJBgp)4Tt|?(af^-+;%Lzkcz)R82b4d@e$eyh$PXxgj{Sf%'
    '1>FxQe~$dXuglzKJdeloa+W+^+4DGJc|4ihjOX!qUe1!olex`!9#85Bajik>2yv}}YX=ssfolgAtwCxBajijW2XU=I=Fj;%W6>RW'
    'zSp8V@OQ?dJMi};t~<#0B(6KicP6eo@O-buZ&-uS{f6`B$ZsfruKNw;&ynA7{#^GP%AX^@$^1FbgT?b^G7o0SoAEqYJa5MHV3xcY'
    '&x6_WW;_oT&ztc)m@RJ>v<90t!F7kYHX(I~xHchm2a7flv<8bd!L<g9Ho>(9i#EY?k1{tN*C}Lf+@e$P+<084;P0VDr;zVqT&Ixl'
    'VO*z>?_pf0konuVpHcoC`59{#x}Q=09QhgL&yk-|{v7!k<<F6yQT`nHS?1D@b>HmSLfflWAZ{n?R=RfniSlb$@^-@HPrKwN%Jcbo'
    'JDWYrb=&a+oq5S$gq_J;>1LdHl6&El-A$$4(4D#e2v_Cjw+gtOoDu(|TTJ=$;`4SUbEa!?PIcF+{;Or|lU;*vc2J(r5B90<?_>8<'
    '<GVf*b~byin{-S$cg~Qz%GejVD_^MPF1W#!vCnY_MpbrSee*yWyP^A{ppv`egXY4{WX^Yueyr@Cz4>>-PM-B~%S!2U^ETEdEX;rS'
    '4blz{m$Apcm)yRtap*dT)EadC!lsGn%)eZlfO7jN507&DdLAC<@X`HI4j<+Dc@7_~S<rP8yk<eyO{8X_>lYRc1vCFhL(!RkSq8+e'
    'BP~PEy<;r{vFm!?8#C&9c~FiWmj^NGs63okN9!YWodszqNN2%oB6OXFYXMllh-)sG`A3=yS}UPzE|~e}<wv=3J<p7C<0#LJnR%3F'
    ')^p=1&x~{6NQ=>P;8=@6oV;Fslmo|F49|@t%|+K`@R|!<mqD7#p>!F2&4sSZ$lN~CFDx1j(!!8NqibPEqruES(r9$%pVtwy-zcw('
    'a@Q!YtLLs!UKg|9dR`aju92337;jWxl%v+`i*nSszKHQgd2E!U*6S;C)M$N&uH)eK9lDN#G#aeqAdLp;IJ!oIbR4N!==z04(?QxC'
    '(sVHMuWLGZtq0O{bZri4I*9q_J~>owS<9oM+%ncOP;Obzqhh8VX&HKM8Rbzi(~h(ZoI}>N9zBPQ{eyDID9?;Ic9dt<bI3T)j5v1P'
    'Ka$5r>qm6m2d^K|bswbZAl(OPI!O1ynvSmf;58$<?!$BMSii7nK#2KA8W3Xskp_gcLR|yGTA{81A*~Q;K#2L5K1A#^(lQV`jq;X='
    'okm&)%Kc(3L(Bc*yd`3%^}Hp{{UR*`G14dxj2LO84IxGv<$+O-SNA8%@gjd>MjGXTQH~eofq9Ns*MP82gx06%IuTx<qU%Ih1423x'
    '(tvcG2x~yPPJ}feT_=*7g|1&%G$XuL1!+cTt%|N0A?*@rMp(PlH6yHD>Y5SOE_KZaGyh!6&@~Hm9cdQ$I?^ok>qxV}S_aZA^y^r&'
    'K-ZCGp<hRu1=ccjpJOda_c``I@;Qo&?sM#a<a6YI<a6YI<Z~1k-RIc<^<Djf1$4>#I|~lAH&k3>ifc)SzupA>o@+OUt4X1KpW=I7'
    'aeWGFQgJN_Ya;Reowz1q+tZ2PKfb4v)Lgi>V%f(DJ<FnDAx+1!2UpOuY<qA8Jqv4C7A*<sO7Z=gq>f|RuPJB{wmq6cc`SQ0$?{nC'
    'XyWDJI*4UoCcSJn&C9Yc6DpfU^V0P%%bs9d|FZ1~7W6NqdD*liJ?C%Pe~IV(E&DIYoPT`(C7$!Q?71X$rTCspQdf%axx~wF*>g$i'
    'N_@|y_&!UhE;fxUzRwb>i%la#noE3-GOm}|_9zQ_nPrc%vU*v3kFubbA&tzUCE*-<d_N_bV~_8r#B=Pn{ggtE-LjvO)LAThDDnEn'
    '_fX>Xwd|oJ>ucFViE9e+J(PHTrFLN1Hwo1}uBln}O~Q4zXln6&lTh7lnwqY!S@ulh`kH0WG^ww}_e_)eT71tmuCHND&7vjgIc>}S'
    'NK!Yk?2i<3+Lry1q;3-5ABpF*E&C%$-6XyzlGK&rdm>5ySoTEXIsf>cNHXUi-xEpZ{NsBfasSBm2=RT8kgseSoMj&*-B%V3&aw{@'
    '@|8t{Lz;+X4>zvIS@v+_dYoksH?GH7_Hg5RoNW)cpvT$va0_}I(%>vw64sS0`yKHdvSq&`u7kw)J1VP##P&OqIb_RzM<Iu7+3!f|'
    'AeKFjcuwB3#}U_+EPEXBoP2zbBkoVj9!K1twmpt`PCmZJk<7{S+`DC8Bi*+)&Car~k?vcIW@p*g2>I5c*;)2ALcX<Vc38iQ?<vRi'
    'JIkJOT)(sIDJS*2_?~iHzq9Nq$MrkQo^o8j!<t=OOF|llZT$<^IO6MH_-`!hU*vD%>tFb9Z0le6Z{q7;_-}0MU-)n0`klOP(eJqb'
    '<NBSv9@p>W^|*c~{cq9l`1QDcC$Go#J9#~5NtX8?#loWTS>AsX3!BClfB$hTEE-?@{YSB|X?#2uT;tnK&%Cn4pWDUlc{K3I63=F%'
    '>%mUO*yjux@5k7qXmQid>3Pk%y@F;QG1vD&OQ>eoo_>DOpSJ(%W9m2Xl`{5Ds<(1Q?wnBmU;Z0>pYY$LoNX>E_T|*?gYT)|N7|+H'
    'ueBp`^RJ}7o!5Mk)?K$3(5a`k^J9i>R9taP+7IgXGHNxZd+r?AB+q=|fU$m^$W;3DfuU(17wnPre8a9@Kh3xc+Ar~Aj4`xf<HxBk'
    'led#GN!zn#`!Pv)7QZKcZg>{ICweY_Rx;nY=l%JfGt{4p%b-6Ol>t3h+Doa)v=M$Rw202VsZYq&tM&?dq;%|b@Ll?zuKV+Re|{yh'
    '$J4~7g?>%VIx7F;{4|fP*-6guh7-s5oZ(Ws=fiyNeF(jE;fJ*LwwHvR<l=tyLb1=qO{2fB8tHY14fOQ*A?ew3!QMls&L85(w2SD1'
    '(IfqMdm(jd)GK|@gI&(GxN8PAFD(l%n=FG~PFXfy22{>aHeLo?PF}XE?zv-@`SXtTa-uTha-uTp<-}!1<qUSx{`|FlXP;YGLrb=f'
    'NcCvVPVWDI<qQ4&*XQOJ2lGF=oylyW*Xs?W`yV<b_r0GoU|{aMLw53>FIzn_<@#2(@0-pGG&{*%jQymC&t0sdHRlZUIrdrfdeIl@'
    'Ihc7n(Qq4I-QKTBTtPo>9N@pH(RA<3kE!77r-hx=z48~+y&q=KjYswHXG8a(TkroLJvZxhVJGKc-gE7S+&P#@PU)m0`}v&GCMv$W'
    'I4ys$tGSh(7L%*`Iq|yiGNXF&y6`fidhxpOGNXFQy6`fidhxnccg+^<q5kLn8`cZe5!DOT5!DOT5!VaV5!EZ$N%`mY@8`e$b#&60'
    'p?+_6-A**bo8I|4ry(YM%N2`0OIa7)-bUyDdaBO_ZKH{^XQhmRZkM+0BgXi4ehW3J-p+IHx}D@~FZyjCzt8_J`t{Tq>HJr-llx!v'
    '^H*s<a@**yy*-ZpSiMtvu5{i`Vt2#s9enJ@(Bk23eILD$Y7Oh3wqwEGNUv|4>esUEq7VK#!9RB!?f9TiT3>Dto!j28huuMKzZ&MX'
    'u>JJMcgN7?JNFZ}6Yip2lW)`Y#U-=GdZuDCt?b&vui*-IQQ^sM=0yi+##x^f$h!0T>VDvL=XJz>2zBRmJd__o-Fba=Kk&NqIwC*F'
    'y4P{<e>RQIYFR+o54ul~AFxk!KOD*@x*v3(AU`0VU_S&q8G{YDbCMr}&85dz4@)%^%})Bh-8=gDesCL|ciE_POs?5Uo^V{3PCie#'
    'o2pdnmpdmN+bgKb#`eCQTt^Rn+$(L1G&{*zo%Y^juj5yDvmc$6wspF_lR7_LlAE(+GUeTk{bo|_<K_{zXVDjJdeiUjy(iZWzrAUW'
    'KQnqeUHm|||Ibd^)iW;5uQ%LAS9k31{jiz}ukWAcUGsMGzK#B_(7$gpsrTffbiHc-QNz=AEZ7I=rR!JteD!{+zI`g4wSEsJxwyX;'
    'jr6%VZttLT_xJJd&wl#lpJ(NMpY#{!-qbbKlJa&k25VS6BsT`jW~;ezPtBq4)_zGz9iQ&eHLY*nE-Gx`mX_N|Tk20KDC;ZkAI)#v'
    'SKKGaZ`@bhC)jVnSKKGqZ`@bhKf2$fueg77zj0p`71nnDx^p>w(D)WQl;1QTBEKOYBEMlD>VCsMM1IqKi2bJf5c!SU$sG3n`jfpD'
    'vx{mrSeWt;nw>C^RaO*x&bhK%vUon7`e}bcc5?quI}S?c$gOKmNax6!ooFt<>^RQrgL|mkFZ-rG)a;_diY`-rI*s}Bh@7_4?Tc>d'
    'nev*Q^ZBZAp5>_Ic8yy^`)?mg*sku@XBPW5u&Nuqd}zwHX?9Uz#x*JJOFp`D6(!@$jr}_L`O8B3UE{CQelXZSQKgN8XmGXNrT3}g'
    '8vHzo8l7E~TW2(@{J^wd2=@M*?w|B=Nt^u1)BSv#yozQX(=lb_@^(>SWp~z-3rg$WJ*Nk4duo~2F3Y=XJ1@@pncIoBa#H;%skTzG'
    'x5z(t9lbrbYub<G?d08CdCoBZ?tM?~Kc1TF6O(eTESZ@0%XvGg?;nrso2zf4J#F36&1-yH=$}11`uSt9v)NPKkpCXx-nsI_0`6Px'
    'L+t0^Tkb>b=ipoJL*!@aTkcQY&(gQtpSqv9Z>0})KXc!5A0j_<-)6HXyB!~_q6;7T4Eh=ST=z5fx$bA=bL?l`=h)A>&yk;z&yk;z'
    '&yk;{&kxYoCl2=O6e_zK|61?stJ}F;?tiBFeyWPAQE55#ZvQPIJ85I9UpU;ix0T&LCoJ>&rfw%=>|P7I`*C<VH~8`q{(aW%Y&PSL'
    'tJjbAUAi_m4xGMhKsqMW>|{>5_JWpvetLjL{c3T#Mg!R&{JMi*yRnD9{(eH*7wC2cH|?<*In6hDPwLj4p1w1>y^8+v(kQ={WDo5g'
    'QS5V=8|cL$ozi?=-cH_!KYupHe}g;dH&uJ3W5ple8|%kB!A{<dCKrzI-(7k4w+m;|lC$RI>awo=z_k2%JNX7%myGxQNM(2P#%;N{'
    'C(r%t!AWTzIBzF?`a{ob^L=_{*LLe7AIBQ5sL>euq4(c~oxH;XA0Of0;r%puQfohF+(r$H$ENeIU>~5KUw)VKf5LA4{Qh{)ZdG)('
    ')=r}rSB@2S(uclLJSNwNChy@1{m1%uvbt-~WFifD<6mX$3tZd2N4W!kyrn?Kg8N^O3y+2LxgHlD3+{6i7aj}gb3HCR7SiW>TzD+F'
    '&v9HrETqr%xX4&=pQE^hSY$Gd+|ti$y6H6v4iOhUMkp>QMkp>QMkp>QMkp>QMkp>gMtWROjBs2~jP$rj`*5{a{W{kxZTe==WGx!5'
    ')Ij-tEP5{2N#pmyIxM;m*LH(GXweg;J{Z>%xrS@ee7S~e(R`&w$;%nnf2GD6*MFt%8GkO)VbOE34vU^Eb=aUG#`Qa{$Jz9|pvPJD'
    'yS(OW(TKU`Yte|g=4;W2rH06T64#5lA1r#Y^g~=P<~pXOoJfbo<<xapR8FMB;&MvuIOtz-y-aF+alMS|UlzTL>t7bVOlrh&O_^)N'
    '7EM{|#c@qp>ctjKIcR)RV~y*}(&uq~S?ZD&eL48qqAzn@(o!$1!|L@yIxMOe)|yehbR8DeOJ3(1oJF7FdQ)7V;(C)!pW=FxMW5n&'
    'lSQB6`m#lX4w|w>gXWsDO@rq8a$JMvnzBWMmKvPY8Do01jA>kt=5e&>(NbfL>(NqUjqA};bF}yY>9D#VkPeIdfOJ^w2VI9ne!w~`'
    '@&nglxxN$EgSft9(Sx|YW6^`8zGKsa^7@WN50V<0MGxY7bX>ERdURZ~<{Gp`vz8ikT(jmHv_-S#8ni{T<{FuNPb~U1*A3(PwR}%3'
    '`Za%N;`%jzPb~Vid{5%~wbT%8e$%yV-ET;TMSjCNtnN3Y!(zW79Txcw>9D%r<n^GZSo9aJr`Yrtu3^RX7pY;z^%tq9#Pt`cr^NLa'
    'si#=<m!Mf&G;XP1$2D%LU&l3WsaeN0ZmwC|H142T+ca*jUt2V8u3>Q<Fs^sY_t2tu^LH|?cguG&u6N7#(4u#99nhk8bB#5wcS}t$'
    '?q{UKB0pmtR`)a3VUeG89Txi;Y2Uh^vG%R|8SAjf&s>M)8dF^F;QEC{?~oc(T<?(jMO^QY8dF^F;QEC{@8J4{MepGHg-!3^dbdRr'
    '4;r^c6PJ2-ToadicU%+a8n;Cgml}6m6XzPYMHA;5w@nl0IxK(ZE&4cr&*S>IeCOl(xYYIH`nY`OE&4cr&*S>Ie9z<hIDgMA`nc3y'
    'Epb6wxgHm+!|HKCIxLC{)?xLyV69w_3({dxT#ycn<D%=ZC@%bZvX=I!9yQZ-wZSf(?_F5mO?f*j>|~FH`oB6d-ESdpXEGPNb8bAr'
    'mD}7%*xBrv?$vARxaA#R5OyYWk-O&ny6&GXt`T-o;aTpB=c>87?>-^yOy&aTN{(^;=iDmnq|C>BTP-br-cEk=_J(Td@AGzY&pWr('
    'OYfhzv)M+juwN~A?Efwoc9PGTbN-R;U_K|<$!|WNb3*$2V4veI?olCKzZ~of-KIB=ch_&fLD)&%|M_K|)DL+(@zulSYNme6+gKBi'
    'uUY25L7Mg9t`Ww+=h`&V)^+_|YTUYRZqwq?nq|JWTGy13{);tbUH?VeG1ixnc8u;Hv}2^jBfTDJ@kp<inzgQ*TeN$;7F*Zu@tS2`'
    '2DC<4*ITjXi}Y4q^F?|qUKfnYgS1_}JV@Kc<>6~=k#?`^`&hfz^?j_}>-s*|ps{Wq*ZL9jfV6(hJm^|KTC-esZMd$<A`Km_`PKDJ'
    'q{(6p9ci*i-$dH0UVgmJ7wNOQ_KM4ov{$|Sat$n6Gp_RhNb5&D0A4??^8i@uM?3)6%5~k`!UiA)1F->k%`##GbOr;l0cg##tRq^('
    'i}Xaac2(CCk!FhZM6`Al>4``))%8TYZdb1_UZaZiQ(YUy^+jt`_4;CM6xBCqqnHgq`~YGDbbbJ_0hk{^>(h090I>mxACMX`(#_*6'
    '0bZ-Fvjm6<K`a4YtFE&Ic&)n55}-B9+$VT#sjlB)O%rM8x~7TrJG{0O>vx)_iS#?XCKqey`WjNCZzAmy>6^NCi5Ua5h7|cn*DkSt'
    '&^lb*KXMHzTK}%|26+9u&Kn?>0PzNR&AZMUAeI2}28bm<yn)nwb=};?9-uYLI(vW_6~rE(weUK7fEX3T9$-dAXAjVtW$8~{bHp0D'
    't~p}846U)%^)kH1R@ck$+D~0C!)rfvy$oxPx?YB~MdVMUEn+4Ct*b@;MC)piKhYXbq(7oHo`^|6+9L8N*A{j50PzWUeZ9^n;Pv%7'
    'pMclY>wE%Y4=|sgvj><@K<okH6S#(}>*f|#0W&j*RnVCk#46x5%Q~xonHj_?pf$^gRX}U)byfkbS(a<_ktV3?Q%Dm;`V?L>tLsx('
    '6GR$1(gbyV3Tc8!pTe4;u1_IN5bIM&`$PJmuKi(s5UrC%`XJK&kUogCKg2NT+8@>jk@koDuWNtE|56h~tODX0bXEcJ40!#%&NJZk'
    '`#R5nSOvs0;5GX?&wyD4oo7I-0_GXGR*rOY3)_Gg9-VDK3=d)(@S0_vZ9ohUW*ZR0qq7Z|;nCR!#PA@t0j*i)F~VB8ejRD$=sMEM'
    '(RHMiqw7d3N7s>7j<4%lIo8mTR<2)1S~=FxQH=C>p%`K2L5~q;9`qO;ih0mtgyX2k=upgq79$)l6eAQzJw`Z=r@NCHmUqLSeWw8P'
    '3>Fq5&O99cdVKVI&KMjnJE5}*mc8XUM}gUiIP-wCd)q$hLA$r?oi5n`%iihy{+t1b@0X6AWnnE4dtlk?o^uzLz3w@8fmsU+^Pp?x'
    'mVMEsRvzCMoonTmz0hTO;(MX<@>uplm*wGleSH6OT(&ryVcGv2mo3g_AWp-w_de$|EPL;BP6M$S7Ulu-5Al7@xi)Rt=Unmw@qNyv'
    'Hf`D4Je1$Ex4G2T<9nOS^2hf!=jE3gx@A9ey)G7(!?K?_u1lQd!26k7&H@Nrhvh5)&UIMM0^nSS<tzZnbs(0*!aN`?*s^bV(1I=d'
    'mP;+zvTr%pf-U=&2QApLS2?e*ZLe~!eaH7Im-V&mRUYbV+pC<{muuYd{mD_?E$oM7e{x*+IQwDSpB&ZQ!hRqQBz`sl=RhoH6G#pu'
    'el`K;KrCkya1I2sA93aZX|I-j$fdp?--n!QueN>2rS=-zhn#D#mVL;}>ihA%$GJ8g-+NqY)A7B>CI4XAdz||xzW2EFPkirj?jOlK'
    'SoRy&ePv-qEc=ZkUs+fY%YNh7S8-MZ?>8PlD}i$(ma`H#H)1&}fpa6avl0R~VmT{;b0e0s5;!-4SP={Jfcb~`zT#5rjPEPXwNA^v'
    ';#}*r?JFL%PTRiXLF=^bD;~5?%U<H#pO(GECI1lLOI-RhzL&W4r)4j3t{q$U66gGbWiN5=Pp%Qi_YX(DwXr4f{ll?u<7|m-|8U*6'
    'HnzmFe>n1OoGn3|iRJ7D&Y4)wZs44W?d*oYnOM$lkeo^U>;}o1#LsS!oC#t}EX;$hEn4;o=h~uWpKz`%+V%<O`g?qzaIP&{_6g_O'
    'qGg|Ot}R;j376Vpd~a~6?Z)>8m)dT8Z*ZyYTJ{F#+HQPraLGT!_Xd~RZhUWW>HqlN;N1UG!;S9;j$&b9Q7rp`qgYs26w7|#C>9nL'
    '#j+nbjzyeB!P<KKED6b_#Ltr8T#Dr^3C^Wh&XV9<isdW`&ZXGSk_cRi<tz!#rC83AkX#C4Q7p`ZuB}`42jIW4><_?yW7!{o|HiUE'
    '0RN3`e*mtn$M*-2zlrY;z<*=gAAtWR&ZY3{7A{3zk8>&VdYnrsdp*XbNEX7vrO4|sE=69Cb1CwAoJ)}`L|`5)-xrFVja`X<Unq7~'
    'b|v<Gq1aj3mDu-%V`pJk;@=mF9k-J<{MIG2(j0Q$&SvLR>q|@Mz_454b!kthD?9Y0`>Nfa%lYpt?w&FXnw{j~|F(93&%<w^VJG$R'
    '<D4b*@10#ef5Po;^#1eXQynM#m;VOchyQmA-L!nPpC_XGpnIbG1Uum?POI78^A+o9{83X<T~D_c)9~~AQ`L$$<evM;U&f_n(Crm;'
    '@75k(vs*(YQwRBc>>^tGyKXf1$zKXP$!)GIoaQx})pX~&u|8iqi?%&K(C6oaos2iGdZe5?I8F=ClK0e~%bz9hsXv!LE6L4%^UwmH'
    'yVjqJ%7C7W%7C8B?QFK9>;Lpl`pe~Ga`TQke;u2Sfpz;Qdi?Jb{d{dT^%y=N%~5N1QkT2m=;-URfCj%`oa1V+y^2oTHp$O_chS0{'
    'F}}=GsM{|;r45ZA5_a;AHJMiAb>#ijy!-+`M_52LYj;cUpSP3o_CI^h_W71Ybo2LlKhL8*y(W3BD%ja<9ru5)tf4DfT}!fTygYh2'
    'W!ZRn^m6jD@iL%t^0Fnl^dBp1^tp6YPQA>yoO+p2IZ>HWIc1r5(UemL`W(~(x_nHRv<%2z*rkp4+cG-q`{5}kfb4T?4e|Dl(mB^C'
    'uPN(x@~z$YO-KK&?WU5wGgFRHw--@K!SM8({ZscIzTKEW^ZwqMUK;S2u(R3aG@-{=^z!V2TpqIM-myLpIiD`NVPx9x<n1JvxOMP2'
    'uP<z&hkh}}_fu=hO&FBszVdc%j(OWq--holZBx7C%9+fqo@!g1=Hl{pGRHh~-&8-}40YjUM)l%#k!9BF#p@!=tk;XzMV48w7q3e;'
    'd!$?0x4iq!85hEOp*o^^p*o^^p*o^^p*o^^aXa}=FPJgSw=H|9=bGU@m!jKAT|Rxix39}?s@JVw`fh7>E(iPWD4&B}N&DJ$%W;+1'
    'uHeQ$Inw7VHqqG+Oi%e7-CjY{e&5||XWQxZ))P_<QL_{F_>3z3{262$X#284zg}z(HR#)xF8@PT*hPgC=(Z=`p+>JfnrlOjtk>7K'
    'Cv)hFl^yBM&c7>Tuc67AR{njMPmT9=^}bq0jhlUuwk>%($&=jnn{{3b*iB2;4Dj#gN~+LiVCtW|oynBO`|Oc4{KhkKZEVS(ruf*c'
    'qsKb*Px+I)oypX88}D0ByI#GUc->_kbw9|u^Ex6wgu3%OB0uoD%R1_Qkag$v)&0QhUQ}4mEuFKE&KS`E`T_X_`vLhx_XF|?@&ob-'
    '_Ji&d<Ogmide*iT<Gr4>gE~ArJniE&JJF8{+Z1}8u8MnL+*;bUu`6MF4_$J}#&Dkd6GPH_>UPG}JZ_Zdy4TXQCkCW#qh=@U!87+Q'
    '^z6Z2s(;!ry5z=k4%x|AV(5nXeq2%BJ^uJ2zh(;A%V}!2*1m18?w<H&s@HMWQ=J(-)A>u@PTIXur;qjdx(#&SzuQr!$=NyX@%TC2'
    'QU)?_CvDV%BNqEMY6I0gshj`(7W&gI!_xUw-p*$C(Unh?(4MY8=lZE1sulUM(|TIerCnN{U~i?`{~hP`?h0<sU1NN%ej9y#`><3G'
    '&D)6<)~V5^oEDbJ?4_npE~GKT%je#)ek(ep?_1u^WR7=Tug<uZ<A)YVUvdBFev`i9{?Yv=eZ~Ew`;GgG`vm(f_=@`k`HlNZ`b75|'
    '_f=8hk#6t)$@I(D&L`|Q-G|t3x(~76bRQzWVIS&#Lq0@)Lq0@)lRn%>Pd&ZXmw9{XxM*xT2GH$|bm?1N{XSZIX#Cfs(=m@`C+%3j'
    '1w*|yRM8C@JKE2MbvtQ?N8dO)-Jj&;3wotx(Cr_n?tsC5@2MJY*ow8ZqW%Yj?4%ug^wxR49jok~zHN1?kLdP~^hS-*elLi<)M@0x'
    'v~ASvgb{6XSs%}cX58ibXZSTf>u9?xO5+vmimpPNbv~xm+_`@k<Ih%`O9LNom$F#F-ba(C49&$W(P(<TGQpqsy_4QPrZ`;#73`mB'
    'W!Gtbtb2eSt2y1b`CI5e<G)Drb$L6<KNKB5(B~g&x<Bn%NQ1jQo72S}{IJ-clN;<r_j$YNYOev+b=Ur4Gp#9iRjx0%=(_o7zYy#i'
    'ZqOTZ=;2S^&1qhb4VdZs@tySOABLsn&)dm6Jh0X(I@nGI-*O*fKL_7(A7VcT-*O*fKL_7(A0j_X-*SKIe&)XAKE!?wzU4kde&)U{'
    'Dy;9mUcQ0Oykr~nGxoXeXY6y`&)Da>pOMe8pLL%jKVzTkenvh=ewIEj=O%W^bHDqj<<&F2e~|q>&AEHB*U+oFcdnm7L)Wz-WGDHk'
    '*Xxz|yl7ST)2D0G-)MFc-<JPdnu~8HQ_g+!<|z90u;tKB-hqbiF8AY~YVO45v+2R^t)QK7K6Ngem*aerHowJL!&3G@vy*=O=e5&)'
    'KVH{O>av1bJa;LylQw+(g7tJTH(SmX_vnz8S+{r7U$5`v=ipV`?{AvuHU0I}aoxbQAJ5xGg_YbDnHi<?=s}e9K^uy`^W6IZdZ*f$'
    'RO8OuNqqnM#3a9t>;N^IF~YyAJE_Ia@#*`Mw-d%-chM@(7*ukT|1i}*tAe|+=EC%S&fCd5T(8@FzyHG)Dp@+xw>dvkNw4u~-Xm`('
    'v6y!2%v>xIzT$y~8$4f8%^msbcb*>(c2VI`?$|X`>C10V%f0_~s~>#-lkei{XV>Ju3u)JJg%8c6>$l&K>(`p~S>(U{pQ+ymBh&Ka'
    '?M&uU_uJ7Yy6@VYQov&&eXhra$3psCj|-0l_c@9Sj|KNRiVKeg_c@9SkA?KP9v2=9?sFWM5DV^e6c-+gqQWcO6=NH?wUvKvisFJ|'
    'gyMo?gyMo?gyMo?gyMo?gyMo?gyMo@q{jut2*rilN#A|;*5Q7=(mp!<hCylHq1)T(|CSF(_f@-XZ%N9^YId@w>GB3E{F<gp?%v(2'
    'h&C2OJDWYiZQXK!?*H(wxjte{^Z9<Pi|h(+{{73T|LYTS*GH^fmHtMztGE*{D)#SNZMWpyq3Ie2-9EzIID0jH{7Q>lAMtaOHR+gN'
    'vy(oe>S+UWeMB~UyqmVCoZJ7yfC6ME@5~+d&hhPP9e2B1maYZU?V9e%hqut^Tc6D3Vd%n@eonE4>YP6`9p~ijZ1!mP+szeSz2Qga'
    '-segMll}X=mB#&Jl+RZLyQr|1J7ViT8vo&aIp6+o>(HEUv)S6NLF)<BVDRn2PR3oydX|Ix4%K#5yKc(m!IJ)Z`jN9!MmN~|C_7`J'
    'f0rt|b9c@1eyix_-ZL@f>w;a${d((U|88Vl$%esx|Dsy1QjN*ft=%KSPME-%eMWm0y_Op|a&_){@{PaIZ9@9J=j}|UraQOEbh_Zv'
    '*C^4&T3%ko9n{5sq|EHT>D~f)JDD4vJz|od8`f~c|1{Bmo8{cz(}tzvguI>2Uf_;7rmFjWn_m~m*ztJjapbY%F+y?Vv6C^<<H%#j'
    'V}#=vV#i~I;}~McV}#<!V<%&z$5F<P$4ieRkDZK>9!DO#Oy+XeV#pb;|GP&WB93}YQ5;cBQ5;cBQ5<nh^*G{~>TyIdMR7zi#c|YQ'
    'isFc3isC3^dUy;Hz8<(88|M?)Bpb^VSRj5M3)duhA<KPq9tqt?Ugw-loU7rSjE$=aER%(O;w+PeeUhvW=YK35R4Av7gW~*8{JEHk'
    '(w~c&DD+&(Cgr&l3&+B_6br|~xfBb>BH1SkE5$jeI4i~3CkrdZSsLkwI5)-pVB@AZ&lBgSB->*tr_Lkcaw3LGFDK@a^m0lbiL)+o'
    'ZbY&!ac+cjAQo<fb08LOM6yzGwu-Y-Hnxg$Qx>)=uu?X*it|X^&vDL5`rN`<aX(u)EAD3tXT=$$c)c)>q}K~GS9-lLbEVe{Ggo@O'
    'B#*>d6bq-pxr;cbA-Rh<r@^@k3#TEu3k#>gIjcB}#n~zgi^bV03ya0sDhrFn*(wW*C3z$s(>RwUV;bkOBx@AsvSb|NT$W^wEL;|6'
    'km7#8JQDJQ&Lbf|ARY<%0r5!K4~Wsy{UCWH&Wgmj2+lcJxro3yShxtzImEdL&N*1P2+4|AxQM`F+1RbXV%gX&&SJ&cEy-fV*)7gu'
    'S=cSfV#V1l$s_T1CeCs3_r%6=an>l#amn{2&T&b8CeCrmcgDhT1%AfnH=ReqenU(b@*CojbiW}U3Hc54NV?xJ)1~`OUJqP>g+t(6'
    'fsI4pTtS>ekX%8WLy#;-oI~JTfrUemEJvI}knC2R_2TT7h4td>mW}la?3RV~lI&KT^^)vXob{6IR-E;cEJt_`E!>xU4=vmme<$PI'
    'mwXT7+?RYOE!-F9VJzGie-Go_7w2ItenvbJ@-ya<bUz~=3HcfGNXXBK0n`1Ac_iJ>h)2SH=4?{X@h!T)WG&*lzho`qx<A+PZMr|#'
    '@h!T4(D5z0KiBasy1&%%<GR0Oz2a;bXT7X!SYW;4Y?$P}ENoa{y)0~)WW6kG7-zlWY#3*~Y;0IyE%<wG;l$)SALqp6J8$8{_<L^Q'
    '#5ikY;l#pwZsEk_dmiV+Bx@As#3X|hj|=9J^tfOiNskL=#`L&gW=xL@X2$fmARY<D1@TBIE{I1$agl5iXCdM`yJR8aI=j@(<2pOn'
    '%`G}R*UfD@J7*!{Iy=|REjqi@%`G}RXCW*)J7>e<EE#9RY%Ez|!z?TrXTz*4SzyB~EE#9R;w%|w!)z=WXT#zw8E3;REScny_%{{j'
    '%H%g?;mSC#V&TfdcVywp<acD@%J_E_=gRnZWaG*>YZT|o<TqvE$^x%qizDKZ^f+S1OphaG%=9=S9tp(}^GJFe5s!r8h#4~!N5muP'
    'am0+79!JR|UF=$%camH1{RP6#W-oOg%{$#Sd-$X>_Lc6(rN_8(O*c1{b`w|mmB#MM0rd;GT~ye}Jw5CgcYnji!p>wabWhE!>%KYX'
    'rZV=W?#>0rdfq<R$vr3bI6b|8-YzP<#JzLd>F$)jog?f_<{H=ivhz!S^JP<Mll$qb3*GRNk}~!suFCzVyXHgAE0FdT?)qLQxwVg1'
    '6?Qh;)Xnd4p4(D?N>gqZ6<+C{KJ9#08h2r5v)8%i&z|Y}{N^!X7ZqOR-r8`nYw+wsVJE(wJm;*`&v`qOY3iE%)Wm)J!3<#+6&ARK'
    '!_IV#JB=4MV#zFfUdi7h*6Z;0m_omoOqb52VQ!5xW;$<XVc77VSNxu6Zz!FcLM#?$&(I!Fh;7rED|~;>Vj+f2=iD&ErgLtb^+LRv'
    'jd|1AJj}eIJ+CBtrn6Eyr-WE3#3><G3Uf+`i9+SknJCOn=}Z(Vk7T6~^M<%Mv_F{6#UbVmadDE}(s?rrBZpW)%*dfVuXIKZ?Rh2l'
    '7DIbRA@&ThOga~YSSG{;A(jbqL1>>Sz5JM2LhPK*EMay|XO=KK$C)Lx=a|mXAw~{!bcm5d9G%X{VUCV7W{5Y7Gj)hv#7rGx7ZFp3'
    '*hR$D>3d%BI^sQ`5Ql^IKGHcHy!R1e&k$>*b2xbKBb~#+`#z!iqCJlE`r<u~5O;)_B2-_r#}VR=_<l!de>0uC!%Usd-C?Fq=k735'
    'r*n6RsYBeIWXuq67H9DAo>w}9hxa<u89dBV>I@#<>kKh?`kq(ZCwNaMoqItn(4n{&odrVN3)-6qv1d99gxNF10_off-p2{~M`wPp'
    'e-QJd`v>nqgt#D``9c1{%nxGoIP;@3c$m}E89dDCp*_=dP7m*yrgM6T!9$!L-ZM?-^f)Vpd9ygPhuBWc?4iBXbY>5;ojS9J_q@`X'
    'J;ZimW>4SqO8OJAI*2{fSsl!opuK~1&IGeMI%k4e9i1~ltPbK#@E%QwGeJy_?oY(zV3rT<5rnuM#N;4<A|?lMJ35ntSw6Hc6Y?kD'
    'BM9xurgMFm+0(f`#Oz_NPiOWJ*N2%so$JGUvguqO-jhw|`Z)W9cry#*hgnm^_@TYpbjA;}raI$?_q;-kAKLQ@F@A_O)fqpu=auxi'
    '&eCA^4DGq3a~+ta(YX%9(qOIw?d^lO4#d(R_DpAK5Z8hC_Cf5K&dgx02JN$ixEjRFAofpZW-$AQ_V7XMA7W;7|08Awb2VrWAH>!0'
    'J$%rfZ#oBv7{5btfI8!+bAXufLmVJt{B#Zw@A-x}K(yzZ&H*CE4|9NgFEX7svoL{(eML+lVqY;6h}c)e1fsp*5EH1guZRi6?5oZM'
    ';=SN>CJ^m;CD}8yhmy`wVAe(FDDd7pI!A$67tEgNtPAES&>l*dJ=0hh%$_0E1#uLJb<sHryl;{oFU+(cRuJv6gIGbGX~Eo!&a_}w'
    '5bc|UxEGyi!SO;&iykk`v>;ZHvo2^)Ih`9sOd#e45fi9$gNO+{6gQ|dfruMKd&=qDAYuYBH;DF>)44&!1R`#bvq_jYi!+3X#l;LE'
    '+VcuAggT3h7(&eAB8CvLxH?0KSX|5yqP^yHh7hs1m?6~nypl2188ghDA;wI<ju<n{p6QGkx{eq#%$^~}3|-e5Gjts>X85|!n4#;4'
    'F+<l;OmTcsO!fGpn4<WinButWF~#vkG1cRXVv5;9J*Jo~)MJX{uE!L|_hQ$i&DpNWg^ddES($O>(83lT?tXFT_mbs1JVp^Sf$=jy'
    'C9jAW#W-7t7&*&%my!dtoN>uH!}uAO^8TE=vz%+GKg-56BE~O%CMo9|EoYK)z7a8v7Pb&EX_oUVIg@5Nzfv-3@iQxBdE#eQN=7bz'
    'W+g8VXW=a8RN}H(7|8fJm8fhs1`_d*@iS664{13gmGh8@fwZxOh%=0zN68s5%XyTX0kfP(DH*W%8I-*ImNO_NXBa<&QgVjzGbklz'
    '$XT`cxs#|aHfAz@?j)*<jhRH}PFl`v4g93#%vQ-y#?Ne({AB#hR>@ByX41kIBIe3+zGPsoZ0AdI?k;}5BxkN{=Sv3W%5tWptgq!v'
    '$xvV0nUb6_i=Qbe>uWhvk~3zUC5xXUiR&I`EN$mV>UFm;mbP;w^}5>_OP#m0oFU73OUoIuoVT=`A<KD7%Neqqx5SL4g)P(>C(C(}'
    'Wf`aVd6ArPvYZ#mIlB0Hk&>f}pBKp)C(9X;(m(MtBBg&UXG8}7*v^RL3|Rb(NbVoY8Ih7R<mVg4&xORkvM`yJb0KwKS(r@Axsb?L'
    'HYO7>a`7{5C7&5T(^m4CmNRVwpJ_YOHt?C2Gi^DaX*<(4@R^9ow6KMkGmM}AD48P5`Hz7qvYr1Jm?F#hkDMv8od3v~BFp)Yk|~Ox'
    '`N;igIrC9+hL$rQIiqDc^O5^Ae&(ZOwBlzzO3pBT=A-l{=d$AGJR;xP7*5MMkGgLy45#IsN90=@!x=y45&PD{aOym#<&0g<b6U>W'
    'l{{zsj9t!i+RoSwJg4o9-N19&&e#n+Ct^4)Y$4_h<L5bYhR1TABWHLl=Q&D-$8w${XL#c0IZDngex4&|cx>l6a?UM&hNEPt;%7KY'
    'hAMuBqvQ<ZXE;jE&~k<&=M3X#ICB46&Ty0rmE{aa&QNi-Fn(?$iiL&ww4B?BVqs%GE$24sv9K_omUA0XEG*0?KDW_w=5OFXEoc6g'
    '<v-(R{s#Wja^|n(KjUZqa{kkH<}c?zEoc4){?l^iujD^<=F`R&>dcJgd`8a9*v@AR%#7uHM#-(k&u5g(O#FPtvfNtid`8KwS<YwV'
    '%uM`zM$XJw&Sd2AvYg2%IYY~tjGQx!pUEg0r}&wSk~55-$tW48_?e6{UY0W%L%b|!GD^-+p5GTchY`ij#)w+ZVbo)1VMHzGFrwI5'
    '7*WePj5v02M$~c+BZ{4k5!HE7%NfLy7mc4m%z07E8N_9I(fAp}oENp6K^%Bd%NfLy7qy&09C%U78N{3yMU1G0EySE*eE&NB8_WK6'
    '@;CAQ>-cXh``5|eSoW{uzlrZ($A4qnzm79$@%`)gZ!G)Q@!wc@QF%Sii}LFhUX)+A@S>7AjPs)Mx`h`F*DbuLyl&w|`Smz2Dw)GL'
    'FDm29*~0kui(?&UN-f_ninWC)wS2!g)^VoP^8KP%+nCb$_lsg}VM=AJgPpK{2Tquta)5a|(a_7c?CUjj{W`Z3&gzk0ck-OoR;s;d'
    'KspA~>?F5*=HnB5u6`@EKBw6KW;V6C>}$HT|DD24n3hu?T<rG*<NxKq*YCsso8&sWeUax9(S7uLqWf?=Vd`34*Tpk_i|DS?O6Y_6'
    'Hypy=L^mDX*X!vE>Fiz|sQX#B9Kzm6H$PUG%kd`M?5`i_>bcojH2Ks4X&i&Sgj)9)?tin6zTY#@?+><$8Wwl)j32kFyMaencL#GU'
    '{8{pz`g6mx_&xD+!?Tic9rfSj$93qrs0{jZaT)aIN_!RER&I2T`%1X1nr|*o`C;AOL-&kc>GSYgsr>`9(sy3Bchbi1CitA#9@_Ws'
    '*?#{SWUrv7&n%|bnm5hm(3Zb8HJ3w6^y1CUho;<b-cH`h<u~<9bE>uGO!R!nG8%K)u#|@hcE%led$8AcR@1%1hj<2f8y)+%u4#Sq'
    'cJlkK7mV>aA6_<I9=)8hY`hGpoS|&I45*yEY{}eb#f@YA+8k6)z0A0rsLXmfQJGOWrM-!s>s6Gt59|NkGi?)edo%UfI?~Uf_RvXh'
    'FHhek%}(-cO-J<in$CXuar~I{ThQ#pCv7g9kg^;<wp*3X<1{;ysqD7QT}`Kc+CS(2R&NYS{onD<L8<?PopJxEI3wL#>B551o~v9z'
    'M~wQ~?^PS@M9X{VnNePM-c>p`9N_boTWH>Qg(;5_?7ehvw*{Vm*g-c9Ug|l7ZPa@2(3GzT_L1(*5u2!cwM)v>g_jxCE7V1nS+AF@'
    '3okROSEvgwGp-k}OEq`=!0|pei|U2ysMibC5!VaVQLh)SBdS-hlW%J3)=9n{m_@b!)j91`G&^a}ulaG5*I2hui=G|Q9F%4!-^JK_'
    '`}lFi8mj-RVSdepZYTMi##c`C`JCO<?z)~Szo*+fXicxFp0}ytUjAsZUpuecMTN`g$ya+)vnyQAw==IB<kxF#r<N~FO|{*;T~s)W'
    '&b+24y?x8wxw_nc(kTCpucem#+N6w4-cIr=%U@gUb5K9gbN?FRx%w@%d`Iw4-cB@#XYQDg(;$-eWaXxneh=imH1&jmskWQ9lYHI3'
    '?jG&)b^9oDK~JxP@1_?X9#22iN;D~MALqukTtYvTFDc-4=XFGWkag$v)&0QhF6*fKf!AHuQTGF{JFg@5L#TTubDX>Oi*jzohzZaS'
    '$S2qjx=)ZFkWY{wkWY{wuupV9a68e?7T=!VJEfxgU#-O{7opk7cQ>_hpLD;$X)`CJJey`G{prsK+IbDDoO`Y1R=;<XZYSkGwNW46'
    'Z~jboO`4l(h?<?`>rQ#MygQh?+d=RAFeujsB0I@pzB^@BE{B<DwJ#3u?|BT}PR2i<@6YSA8F%uT3w;~4jV5#)lD5NnI~i}hw|BB1'
    'Z)~Ero4a_Xy|Vl4zDd4M33igtJZ{`vpU=#=@9!%1dFk!+i&=pg&fAH8`oPWOJV&&Sito;^BiKXlzgLouXYzKEBfb5U*|{8PGR}AF'
    'XL@#`iaTe|Jij(S*vb3Quy~QzQY*T5znks%rK#lRE+3QTkn?s?VMEt`banSbv)2o_ucS|Oze!(l|LA_>zLGxC{l<MIeWLqK`ilEU'
    '_Z#<>^oi~_?yH1#Keg{J&;09tLq5cQ(|w5ihJ1+phJ1+qruz{24fzoHP1?KYg*n6g8lUR!o?5eL@oE1hZ11Hte;b$^Qze{RxsxWQ'
    '%$sH>|2_7}*}4BFY+L#9gZz32-Ogrfxee3i(b6maSZY^t3yVh5{@aHh!al-HzHD8tT}tBk^4^(gOm(|vX?YfU{kN98?5majS-PF{'
    '9jne-?)R*#?oQi0E%k|RXI#B*Q~kVSJ1zLWr+;UDpm*!`OWVo3o%9P`i+knzg=DQt!{QRZCVChBrGK%{Qw2NGVt&=Slh@9Ub!$4T'
    'pdWfyJh)HeL*E7V&)W%G-f_)H&z4tkRqKzYAD^C{V{h(xv17{N1iPHO^u>w3Px*;@oHERhL#nucoi-(XKZ9MveK%>o=U&RWE^p5C'
    '8sBbuW`37+{F%3tZ|d=G6Z|(--JQQ<tLG~!yB!rbr11*&iLS$6D!Rw&bSjX(<^I(DEPc!Usry;_mitrpGxsg`A@+0dE%zbzGxsg`'
    'r|xI&Tkb>bXYSk6UG|D&-SB7MIfS2epJPAkKF5C6eUAK$eXjc%`yBaM_c`)2_Brx1w~ugdT|BR}U48rD7<F{tFh*7E<o-v`UE$Z8'
    'RB~TV8kV+=x?RQHe(^$Tbaqkc{f}`yPu@dS`&NT?GIl-lfhoDMYvSkQ?=MPyuG^K|D+luXG}d%=n{M>`{2;rMoAAUa&-hhwweH@P'
    'D;u&Cc49`=^`4!m;TFEXDV?k8c3t=0<~=l~?-e;tWBQSs=^&?}+esV#?;{raergN#tUJulLH5)0%>zpo>^iQvOJ47;?i$Tl<NsU9'
    ')j4Li_d~FgZ)aVrUcOz*xLE^6`n*RC*Z#e&xp$A-30t`Tik+S_JlZX|dMzDfx=O#J-uZnqf}Qk(3+u1;{a{6RNssw{4Qws<$&Mv{'
    'Po!WcT*tPbW_zxqhMV%mR9}Xp-7BANrxPEnQ^r2ZEqr&0=XLA3&Cl=j<A>U={SO;bCLwPp<r#hBYR^2J=;{ur<C;C(wji0~%xp3}'
    'o$uuBqQcYM)5DH*cWnMgfs6(BIf_e&1@}3M3y%f&If@I9h4i@|7aj}gb3HCH7To73E<6_8|9V__ETqr%xbRqHvkl$ZyQ{i8K4^Z3'
    'xS$y6aX~RcaX~RcaX~RcaX~S{aX~RcanWOh;(}s?;v(&;Zsdq9o+T^iKAf{CWv(<kX_MDKu*>tMHQZGVGcLdWLbH=O$nibLr{`f+'
    '?6@G^ze2Z<b~jz~6Xki-ZYx%Jt_j(t?fjXOeO%6RpD#PY)qVGg0%RxePlxs^{X2QI`}=`%E*~S!P8jSDuiEb!?E3DkUgg{+@9!)?'
    'b~67O*JTbJ)c9(<8$a8at}oW?Y_^{3ddg39QT-Eh<BbQFFG<H9x?REDee9xiZ@{xA6nkc@vRhcVIAyo;b~0!D`r*-j&REg4u0GNK'
    'zN)MI(&CgS40a{=<CrPAF+dW>7jIkZS=PNY;@d81-Yjn??_SO0R{8g^j(dK^YQN^9ihJh1IcdL~w-evqb?SaP=-X=Uw!Qg%0_(ct'
    '|F=11s`GX-xB74Soqldr$zAx>RzHWW;9h=tX>R<+?c`l*SK5Xg<O!?0>n>d7+lrd5%BIbJ9agXtpHw_=rq3bNalPN&>dRl#^;oti'
    '{e9j}>bv!ZWodn@HQejD`U>v-mXp)>GjC_J&i!f6`EJ4Y-J0^)$r$Nz<gw#1!f_0-lQGic$YaN2gyP6!$76)zC}YRtrN@!Sj>iba'
    'k;hKPNRK0r9gh);BadAs)7VY^b$vJL=CcY=98pYB9C1wbIHH)MIHH)MIHH*1IO;J)aYQjiaYQjiaYQjiag=r~ch%k>eBWKmEu1+&'
    '?dvr=8CNV>JlT&cs=9KgEJ|al*_li|xB9rvbn@g=a{c(X+Yb2LxNaxqKW<7@cd-1m-7jbFNm+5tPS(z^9#_sCTt{EqjW}UfI+oDw'
    'qup&!XL5a9HhWBtt$k!mjYHT+yP9wA^K+lmT(kC7+-L8+Ux4j8rT*FM{a@XE|M7M|_tfoVK6`nipK|lr<lWfYVP={u)9fS%xS?>Y'
    '&jB`YZ(p{bZn=G00kV^E*Qbp$?%=rV2zO;>r|%QXxzlf0km@6OJ1Nf#AN}adQ{J^$_Jh}hD!K1pUYU+dgI&!H|8kAb<yLZE{9~p6'
    '7JlJ6k0|F(nX$T{tUciD1C-cFj`8Mh8$9=3(Y^4^ij><Ac6ImLhU<LYYr5Z`xx>$kYrDH!W?VkLc{|BtztwJ<&tw0>eLQY+?peuL'
    ';=G;H({V-KPTv3F$E@@3e|>k?q@VrT;o9z_)7PZ$54YD&_{q-~>bgrhmUGG6Iq~87!`G+&4E7PO_5Qrik8>mEFV5*@2{%6E&V7_;'
    '$n$n`|4&99;p=sr`+Wai|NGK!{GQS2x`SX}?>fD4qg&hmx~4MLJidC|d8~O%aoj_!c}x!#_Yi9yQxta|YaU-c?mX5!rYP<*);y*-'
    '?)g~rnBusHSj(8|ap$q-F~xBYvCd>}bbp(8xodn^twY3Je+N+9@jIZ${ZQ|K9(VK(pt$Sr0E#<$2XNf+JD|lKzXN*Q(K~?Rj^6=2'
    '?$SOymKa@^{H=}G4ZLxjNtR46XNE0&GG~b`_d%>Ox)0}y1Mh0%V*~GM;bS?IY+;x=lWbv_C373fY2leA#~bIFImc^zuFe&s=OV5c'
    'KbLdGoQbvYsDUrF@Tg_^(io4*8D<Of%o%12^UN7$8}rP$V(teE|IGam=by_m!*TwZv&5EiA{H8zQ|F3NIWY^Zm$NJj9eB<-|H*ky'
    '3;)S^P7D7jdCoZh$(d&hBh8s-8zUW<XA2`O`R6zzEtysB^EfXp{T%0|xu0#kH21lMm*&i^rCvH$jOvBBVq7o873=lFTrsK_zs~u|'
    'IB&`MNgHn&_(=<I$@xhOZ^`*d3vVeI={Qp@d1(t%%^B%9Q_UG^3scP*X$w=$nNrCNTlne_M+;vq<7nZlc^oZ#HIHMQua+!v+z*(w'
    'Mt;z_V&n(RTI+tmthMe3#1$hyNUoSOpK-oX@``c3Q8J$vzLE2a7QT@)pBBC`@QN0`QS#Ms23zvgaRyuR)o}(}^3`z$Tk_R$23zvg'
    'aRys*#r!?7@YtLgj`P^^or&|<@;!<3*z!Gz^Vsq|iSyW!gN^$Qv)RaRh%46phPYznH_R0yzv)~t@*C!gb-(fJk`IjYgpv=8^Msra'
    'wD5$I4~+AKk`IjYgq#nw@PwQXwD5$S!L~5llEIEM+nm9+Fx!&Bjx*bw!L~5llEIEM+mgYyFx!F2l+19P-<Hg9oZpu3VVvKV@1%v_'
    '=I>;j-{$Y3jo;>6tA*d@T&u;;I#-PStaHWK&xkA5{fxO{-Oq?C#(qXDx9(@m73+TH*Ex@8;rApnY2o)cj~D0nB##&8_c)Jd;rBR?'
    'XXE!cGil-X0*`0o_X4wRVZ0@?9cR2Hvu$C#1G8;oyd|?8W4tA^ZDG6vvu$I%Ilmoeyg4&j_C1gD-u#`n@ZS7AxA5MaQ?>Bk;XSwU'
    '-r+sB@!tGBkMrLAJ-6`QoKv;M1#!iCTrm5s#|5+BdR#F3t;Yqk-zYAKD@JkAxndL-#1*5s$m^Vcv+;6y{>{S6asJK5%LV?;#>;W0'
    '(Zb7d{>{S6ai-D2%LV?;%FE^XHybY(7;hUB9vE*66D}F=I1|npZyOWNd2b67&Kd7G6V4fL3lq*6ZwnL78E*>{&Y4E}9a;Er&Yi~j'
    'aQ+=x_;C3h#rbggO~v_e$qdK&aQRKy`0)I9WZ}c*cNFKtId^J_BWA_*I3lhX#SwAED2|vb*5in{VjM@r73*<46f3U95pl&Rj)*Hp'
    'ag?k$XAa|h8t2Vyd|KemY<yba%`AKx=glm98t2U{d>ZG?EPR^e&EkBT<jrh+TAnwv@oAh1k2B<w3AZrhoC&uu<besdFyxX6k2B<)'
    '3AZrhoC&uu<dO-GGvtyFk2B<w3AZrhoGa$vtc54%-)WpD=ijM?C+FX(g(v6Vsf{P+9I1sT58tVcC+FX3oF|vxsf8!!-)WpD=Nzdm'
    '?uaed<Bqsu6nDfG<GAZwF^)T8%k{Wpwj9MBam9Mv5m$`jj@fcO?uaW!ahF`NbB}aA$9?*EZ($b|UgzfTzRX?o`2A(<#%_AeM((jX'
    '4GXxP$z11F{Of9W>p9OimG%{`S*!EX{hWh+t$SkZWy$=yDYuIXo4DULtCgH3QNZm?=1TYfD!cPItLu7?<7a?@0R{#bmJt-(Esf0V'
    'nh2ba3!-U=Srcw`v&`+<>WbyP-Lk8umX)+<T$e2GoiWp^f;+Ccq=<@!S`u!6f`}rbh}`*|`JUhJ^TqdTeqaClKF(tpe&_r7oMp~='
    'Kfj-!Eg5eoZ?$$(yx!9WUO3VIH2d;s-QK>hP5k-<yP)4kH(5`xb@RsC__e(!`*n70e?NVv{5tFF&W<Ve`xADzhLyWair2f_tnY1Q'
    'haWU_a=hNn2EIMs*6g@Nw60X9biEFY&(8Uu<k#6XTzmZH`SsM-*$ksGm+qR+Gb+|*=L{X6eZC#7+uQfF1HZLP*Z(y;T4#HE|Ey2t'
    '`&_I)XLsK6`K})L=^lPf8S<1ftNqXL+0h^NjA;6Ke_k}5kFE3S@!8ipXP%Z_*JoDy-$@y4&P!7UoAS~+YfZnOv)1(ceFj@+*D2r5'
    '*>#<7_Ze@>nWtpk`OIpab*D3{<7=RdH06_ZMw;@;J)OO*^2wZqrt8sJXu6)B&REtNcz?#S&bm_`p0e(gho`JN=iz;}oO0$V*?2Mn'
    'Ivd~9S>HMvug|RB^lWf_HnPqGbB0;xfhogGd0@^kQ|6q`K-SmKS!KF@omJ*MGi8<O`irbGW#cJ7PuY0R&+BYF<>&eQaGjrzGuV_f'
    'FVE7mS<qQ}G7Frgr?bQ<ORvwYj_)I#T}+vC${17rR%eVUe@hu-%HMLvnDV!DMls!A$`b4QOIc#h*y}7YXY46UtnY7pUNL3qb>5z{'
    '^pv-!Gs$({p0o5iZ%<iz%G<|hck7&aTJ~NW3d-KIp`h$N84AkYlcCVrdpff^-V@3IQ|6p9z&h{BXEIaXl`_DTccn9#DetN?z??a!'
    'tS{{kWqtMj@HxzSe>m$)`$Ok2>;0juFXw@M)|bvd*ZF)t|6J$u`TTR8&*$^cbv~cZKiBzuKL1?j^W%&(<;+vE`g9h$&gzrtpsYTd'
    '4xQC!)1kBaY&vvSpU<o=_K?s1)%j9B`&Z{nDWgmIQqJh=d?}y(tMjFl(WQJTWpp`TN@x7ie$pAgw4XYQOZ&-LT*~m%8NaljI*ZGB'
    'U7f|{48PCl>a0HH`T0zBo#&^lKIQrOOm&^-=d8ZY^K({T=lMCSPkDZydDc1elx#nrwXU=MY)o{vpU+ySY(Jf~uCx7QOgP(5XI4|T'
    'pU$i<_M9@bl;`9OE#*1sY+jw`<g<Boo|7`PoH^GSTF!IQnaPyrqzo<PIdxW+^R$$erOZE_!AqHcI)j%o|2iwn`>(UIy#I7gvfh8r'
    '%If`(v$8tdPx*g7vt8%^`OJ38|Lbf&=l}W4c9s9<GutWuue1G}|EKfYb^brjmg}5(ng!72g)IP?7qS3!W;Iy=ZC=;{X!F7rfXs`w'
    '0Ayas0??V&agFHgT+UDGjH}L1a>kYNlRD$d`AIqhnevmAai#nuWn3vgNf}qpPwI@T&QJ0gxnu+=%Sw4y%ChQuQI?hJ#pfPVy(r77'
    '>&01CHUc`!s_VsBR?55jGjg>BU@xF80C@pE6JC1(vH<J_$O4cTpflmM7hnsZy#QMP?FHBZXfF_F%XQ8?%?{9+)!Gh_!67@q21nZg'
    'GB{)h_^fzs2gu;`WCxVNAv?eZN8159vpPOoo-(L9uSgkG&MWE+D(4k-29@%PltHDuB4toHbFMR}lvm`lZ7Fk3XWMdKQDsm$uSi)_'
    '%A@M6Db<&<rd(g0HRby1tSRSFb=H*YtFxw@N2N1tDUV8L*peyGSyQTSe2y`lIj?;IpE*yyfX<vJU!d&(`2s$3Ui$*F1LO<X4rpJ%'
    'c0l_AK7U^O0zPw|d_j>h=A3zoH6RnDtpS-JvIb;=$QqCdVrxKWR+BZ*CWx&8nILTq*aVR^AQPmm0i9VLXU=uDoHOS-Th5tt%9iWf'
    'DO=8&bDb^c%(>2%)9susr`vV5oNlLVIcLswww!L~Y`MOjdVu>x_W<_;^#JvW?g8ot>H+Q(-2>bY)C0O7s0X-DbPsT!=pNvHpdO%p'
    '__SSn#3#a@YhRFJ6H*Mqhd)oAe%|N*KdfcYc7QE|b`4}1QVarT>9s-NEWI`e^!v#m@bCBed^(?B+XudWZ6DYIX!}48g6so12(k}p'
    '27$8c+8|JNozH34*>yGubUoT2(Dm?n?BpYSW}fzktc2blvJ$jEY$bHIpR5GA39=I8CU`CYxe2loDF#7j#mOL0R-DgK*I98k2;>pS'
    'An5BSgTU8M=cQBDoeTn9zt6PO{%c!7`%kul_MdHq-hZ|gI;&5%f}91<9Uy0+Z3Q_CwiVi0u&pRJ2<#EGLEvmQopY|U*?i8q&SsNA'
    ';A}RXXHNH58w9$)e4aV^3p&r7{Dn3MbbsUX%yoU)V$l2oZ8506Y%z3w*<$GWlEt9xJy{HL8Ei4gWoU~*E`uxvxeT%x<TA)&q!|SA'
    '2-+Y}7McwLWudh};4Cy51j<5dgTNkv3<B+sHVCvoY!LMRkU`-6A%mdzhYSK|#fwZh^$*((-9KbEcs_!*8{9wIZgBr-yFvX!c7w9?'
    'Y&W#yV7s9m2ipzpIM{Az$H8_(I}WxR+HsKGNHGYMJtl)d*<&&Yls#sHptHwp5OnsK&k5JrV?HOGvd7vW@P2B8!278U0_`Uo1o9nZ'
    '5NJQ?JaEc#(|O?JJBrLU^(R>m>QAyB)SqNMs6W|y=>8<@LH)_rgZh)K2W8{6^&s~_)`Q#!Sr2j_Y(2F5AnQTygRBR+54IlUKD6~n'
    'F$k3PWrILjUpmKIXMOn`Z=Ln!bG*qT&^g|e^(BKqSzm1sIO|L2byL=w3<7x&I<K2N2%XnW9)!;8rv0b$x@rH(An5%kgFyQqXR3Ao'
    'vkjs74rD`g|FaFD{wEuv`=4zH&37OhLjA982+w!WHiWb8+J=x5VH={I2+w^WCqi={$cc~*(N2WtK9Cckxew$-$cAVq!ZxJbAoP^2'
    'RR)2wwPX-DTdNHMXKTqIP_|YZ1kTp-Iomp0s|`X=*;-`~C|k?tX_Ft(27$BC+8|K9$RJR?*dS27v_YVH^>m&#`4MFhs9t0cI1BAF'
    '&pbauTM~MFX-mTMBeW&q$CtJwJU>EP5}qHSEeX$$U`s;tBa|iK$CtJwlwIe!668v>B_UVBmPES}o-0AFge(cU5^YJym5?PNS3;JA'
    'TnSkcawTj@QVfF5vXVjIEUPvMoMqJpfwHW84z|v+@;TV#5$GIjon>W%Kpuh4!R9QhG6<YyC4)d&Wo;0szGM)%zS<yged)Yw$|}=&'
    '*Hm9R@0zm8WDqE;Oy^ybH_--x>Khvbdi;_-p~tVbCp@1*+Y@^Hl0BivFWVD({E|J<k6*SY`teKlq^J25+MdwkSKAZHqLV!#hr)9!'
    '$f3~O3UVmgo{&Rfd!ii**%NXoWKYPUkUb%X!uCWv6rNi_4n^CO6obGXq5ORN_-D$`xA#Aja=v~1Gv(*o$3IhkzP<mMwDax#&y=5U'
    '?|&xceEaxk%Fnm=Ka+C4z5kgMhZ5U_a)%P%UhYuh+shq_zdgmF#5SSap~U@=;!uj)QyfZc6UrS*Y!k{IO56|S4khjfZxG6#AE-Cd'
    'tV;Rw1NBCVRY`e%px#KaDrwITx;Ij+O3L#C^+t+SNqK(Y-YC{t#-{P0f983c`Z~*-O}y*XaNe)J-LJFvHb?#Y%JAMMa|#bSv+%)n'
    'rSeSmcb8w=_4Ctex!+3vTSM;mx#}Se_Xf*QtTPjF-c|F1@9_WD|GfS^@xNVBop;nDAx}lWNB>U#J$~KC7LR)>{EhQ=^&1nO%D<!6'
    '>x%7t)Pj&}dbxV?4L4Ocd-;<_>&}iQd*IaN)!UcNu6-w7Iqb=h@mpEF@=v#hjFVsYvcZSG7`}sEQvJtgudAN+<mB3S{b!ANG@Q{|'
    'th3MO?`!UD-Jj1F|Cj%r{QnmJSNuEm{~P~bjW%%28{zL1{r~bc=>M0lf&brPoxM-K>^HB5_skXh_S}sjKdIN*cluXv{!sW%e_eI2'
    '@81^koV0GRYi@Zt{N1s(I_E3*<li5ub#{NR`Q-!o*_9_gwIF<V|7^AQ?A!Bfd9hwvz5d~QLLR>B-|n{{>{X*Je0^#D-BW#?Wf&H|'
    'epkpaY^=V!_1cipdb7I2pYE;M3ct?&)>yxEW$kYbe{KF6_&SSg^VdMv8DE>f9(|qu+Ol4nK7DEacv08M*Q~FTu9>e>Uo%~&UuQi('
    '^vZie4z{oT{-@99`4F|v^4Mpd{fFQ+8tm~G=jWf_s&)4F*Ip0y34eR`vCY4=IR9H-t+U6@<0GC8IpH<c8UOcK_`hhqwtDIECqv(^'
    'tA2mmd-5!0)9J5#V4eMqKdb%j@b`W%>pgpZ$P2w#?R&-j`Rho1oqdk+orZ@(K7T{?w9{7AvP0Qt$Y(B^AI>K7>n59b=#ubVLtp#y'
    '!}G)6Uw!SUfv@D>U)0yxcjdijuL-%4_`dk-SNAKvFaG-V{fh64zh=5$#eIpdS>G>zU$XCl|KnHnbG-R}sr$(HOW#MnUvwY!{i6Fw'
    '_ba}Sz3iI(o(-RORqX0{w-hc+th4VImTosce23C#Ke_YmJfo}EgRJj$>%-?=y=<R#%k$iqT4$fp{qvM{A?wm;GwxiRKey=h06X`b'
    '*Yn)key2Q~?}=JxuVr6)qS3lP>wCRA{MvcpJ>Ht?%@@wiAE)(o_PjK1?epQev|@9<vNU|2_Dc1e58jsNJ&N^v)#i;$Ll&sXTCZ4A'
    '{hw)9*6Olwj|QthFV)xCcUbRzV}Nykht=Os{=uT~omwCJ#77?u-(eN&?7OO!XTFr5dv?nc4}|Y}UacP4abxX0SiEkvjdNF4M~vTL'
    'll$)PuigiL-~D~$eJJj`zmK#J{=UceQSXDl@BTjWJ{0%8QfadbuCLf*hp(H=`=IxP_JQ|A?*r`#?E~!z?E~+L-Uq+V9#gX~cqzQE'
    '7-F+`dq3o$^g4U(er)yQ;eADad+TEhbL*$p+2iz~8PA5tX&-xR^{V{2NUgKa(q}DN8P0L)YrCEGX#QAM>+Ey#i9c8yJ|}OoL)X7t'
    '+gn;^-z^UQ!{g!1x<U5H!!L&KV)QzDUpis>vhW#rZ@c{QC&Fjf8>^>Y^KzcyudlQBOH*g95AT=y*>T4$2;aH)w|9EK8qPi~*0s+|'
    'k6jTy+i$YJZu@?CpR=L*ue}$9=l^1z-QO$rdm(&xT(KLjpBH*>Gn@Zt#RhD@c(Pw-dpmm3vaq+6uGfXX2T$GGK5^5t`S<npb@qAn'
    'F{_>lpIr~M+YWv^<dg>4_iz7O{{4G>-Py6NJ^k`1J9_sYO^)}<?~mTMc(45a=za5h74M1OH@{c$p6Gq^d*%0p_ATBkzdw54{9d)U'
    'Z)v-AG~3Q!oz=s>={@9q(|bt!Mtey6Mtey6MtjKnruUHcE#AYv_Ft#23h(jy+n7_H%lAaD*H@Q5v^-dw-gfoT&*eD^wa%W?+K*cp'
    'UYol1_U)(g@8I;hmz~i2k?@{&ZFRSU?$7^*)$3k1_smt{{ox=x@6U_!=OVSv_I%HoOT(Uzv_&7^Slw*SU|eVYv;Mlp`FE+!PrR6a'
    '-=x-+%4qxZfVZk^W-h9I54)ssMR@!UvP-_YFt1mAoxMi<>b*C@-vzyG%XLda5A?E^cf2{g&n(v2Yut?oz8YTRn(f#@tHW7;>#E1@'
    'bVvUAKz*IP2ky1QKf`<Afp+%%7ejCKw(B2xA+J|`o&Eg3jeS1+`~dszR%^m{SpDqElNaTA*ZMkp|GE6A_4!PJ-=BY9$o34fTkrly'
    'et+xh?7P1+?&xFLcYj$1_3+30Se8M}UTY5d+mifsr@n4)|A>t}vdMPX_1lx<z4iO4_c`8Mzn^-a{oeXLq<!{#8}FgsXTP_84{4wM'
    '-o|^V_u22Q-$UAGzqjq}+u7AEgYCvKKkQ+j^`7%S>piD^rah;9rah;9rah;9rah;9rah;9j`w_kowRsyct11L4m)~no*`80N@X*9'
    'WJNE#XzpvZ9NNb|zc&9KU#~~l0W<687!R|RBPup+yPbPjx7evGR)q5&$Jp^>R_0z?t+VI(+jf6DymxK2bu*XM-apei`?r6+zn69Y'
    'o<a7)%=LM0T&=V3yKh+EVBOz+53(~JTb0*Htt*ug)^<|G+7D~1y@%gs<+^J9J-lAG*xY+JgdAPP4jg)KZg~41u`GZ8TwiCk{@LAc'
    'g~w4pTfXDE@SdT`cDr<S-VgP4c5UbN*%+Renr!W@uZ8zr1FZK8Z|0eS`Z{|}IkI(4cui@w)=Sq`PanEd?S1}}C#?xaxL9Ye(GA-?'
    '6kel;+iO$a47t80yKd-nd1j-&&R*kY%xSXj*SJ<&^rQDeT^j6&S6;|-EcJD^{~fQbs^tx`T3`J1^6;9znJu`yfBrtFzRvb`)s=n2'
    '-;bkh{QHgeTHE|ut)Dvdt-QYVb@pA`fbp&2d$*z%e$S~cz83MG>$><_#Cxvm;%njeoaz$S!tcMXi?2nz=ejPw7V)0zy2Q2c`>*Tb'
    'Yth-Ui#>8(U;Fa*pTfFOji@eEBdQD4i0VQ$;=1S>QC+A;R2Qld*G1Qe>Jryzs7?7%*XwTWEc&7L+&>z_*{8H_wsYU@`nNSR)!!C3'
    'RII*-YMs3<e{|Z?kk@Ut3EM8~ah<&eJ$P0>tIu$`>^E=ben+i4JGQb1_ZVzHzwpA^YvK+&tjhCIYMo`hZr-92vR<R?#M6gZx82t3'
    'tcP!CTOG2~qwG81YqBM`_r-Pg-e$u^OT%Y4U9Y)U^~y7iYMour>pvMB&Ojb+os&1@XDq07_L{rP361${?%#(uT6gBHubp_;8@aJ9'
    ')+4O(-Bs1@*R^3b@svK6ouQQV?K@X>{oPo5ZYkDTE%x4QL#V|doBCG0uLjs9pL?!aKU=R@_qR)ay*xaR4Y$^F*M_+RgYB4M>+<&%'
    '#d@gieeC<;J;_jOdAfhC_p+b)!d;8=pD)%;_VfMch40Z??8mRZ6JB#i*_ID1tFCV9y~%pGO}Y1taHhuqo6xc{)V*R`9`;0jj$E-G'
    'X5;Rx?|-vxKDEKR^OKv|ZMU}O^{THcm91>-IW4wr^Dic6`}vVG>-#y{p1FUB)w6c>b)_=Nj_mU(yXw5hC;8g>8gU(q+Ql`}b&PB0'
    'YeaP{YUgXjbu4P<Ys7UdYUgXjbu4P<Ys7UdYUgW2b@a81YozPwYgegEwAZF@WeZ<ejCJIi>N-+QxsFs*T}Q5|t|Qk}*O6<g>&P|L'
    'b)=e79jT^N$9Uap6DG7+_PU?F-xz&g#p>@p)H=JK2luG=SgT!laii7$W>M?xGpjf5-VkPnw%OXdHspU(==ES*azul5=Nv}b(B^?w'
    '|Ex)^vrPEyH;=ULeE29kt-W|HqxDX+8m)W2<QBH*C!_4U$NcYPT4z7M-En=wza3^%&ls5h4XD<ceeS<sU+X>xU~`)>c9>my$DGNu'
    '&OUQ{w`EQEE?^5gXZX1M8uWT-*Zamb`QNs0z298>+m_au^SXEPdtpvce|!DPcf;dlr1kr4o7IhTv2L|$wNktOtd1x2Ss%XN8DO{X'
    '{dWGoqF4{MU3c9Waw&uDfHRsy?b_^jA8*dT4=UD!><d5aWA(EvUR&8<-M^>J=6t1h{`19p3p@Czfmvp<Hiziu!<zHI%}<z9?0<co'
    'UBlOAG+I65abEk{@EY1?%SN~5zrR?w*x*%5!uy=DcJ%V0VHWBZwr+Z}oq5~Uo2<v!cE`8a-%h;0_V@L)8~a=R^W=N3=x_D+Y4vsX'
    '_-cE!pLPH3GsG?$_j>sJXN1lCTK(_tVx8^zF9tS*$I)iiFk(n}4j*MdzN0mN-&L&lv0Fy%Qp=9Uwe~fox)-(fHRZbdTKk$(-F>Zn'
    'O{wlht$j_Y?!MN(rd;=;*1o1(cVBB?UtM=!YhP2UyRWscDc8NIb)~Yut?m35oBzWnCvx4X2Xx)J2dM7U15|hF0bO_M0jfLqfUZ0D'
    '0M%Xh0M(s(fa=aYpz9v5hgs9r@72zU%|0`H_^bg||Ljq(o9);y^$M@!gKWnIujQW&s&)4BCypN!-iHjaC1(t`Zl|Ny?d{vxJ*^|{'
    'y6w-cJ+2>lczCV8ydG>bkKGU~6+QR*^>Az1wlTb)9Bq$W-<-b}QtRw>^Zb#6towCyYdhwc(OG_bGOye0)-48vUTU)w8V6gqVWjmK'
    '``XkN>vn~0_S-Ly&YiMacXn)TJMTQsE`Rp?+8G+XR<z~kX{dG98>>$p6nbM^*Zae9SzdiIuiI?lzHQ<E9bz|L+uypM9|qX`<5uMF'
    'tLy8`c}=)`NN`?5>?7GZ0=4I>;kNUH0pT-zzizRUW>u{FeQ%Sk{>#SjSQ~AN9vWuZcOrhBy~m#MQj>MR#~xy5e|mLrUR}>mUmTS`'
    'e(US(IcmlE{qpxA^Iq&5-cOFT`_3L!J2%F!v;S-5n6csiZMAdHc|UxXHQctmZ$$ogN3kAZzrA3Xb=$NSyXLY6t9!cB<~Dv{on8Or'
    'uh;*+7;fL+aj<oNE-})6b9r-a<?8F~v42ZfPj^2LjIkZI8Cg5ewzFfLJ-KkK{d)Dq(K>t1Ir*6_!*foHU9x0gxQ4+t=aYS`ekNFb'
    'o&C=Cr(47C9BZ#0HYV)J2z&Zhy>e4utoOAk{r9!2CXJfpdn4`v-6y^`d=GG+6ulAmfbNsHH+(<nKJmTbdw}}H_lEBQ?vuDTd_Sl@'
    '@x9@DfcnJuhVKFDlejm0Kj=P*d&Bnt^@;C|s(toLldRuCw_%@9&rqLm&*(m(p5Z>xJwts$JwtuMJ;QyXdWQOhdWQOhdWQQ%_YC(5'
    '^$hh%vHq~8iEsC|sN4;C>y%=nVq4^YXNr?5{88HPAu~n4$NQ$j-K033*xjT!ox(<?SSoL$QY@9XKmIyXTvdFX<*q9BMCJc4`6l{*'
    '$v4se>u>kYCC$Znn^W#$ymLu&G2T^`+beIW((ILYRps`|+nf*VL#e~^`;g+WihW3NSg~m;zfSf|`a0QU(RFIyMAsSL?(IyuLy7H7'
    'xkK@;B*me`b|%fC)a_M@)ruWfiq$IYRhrc*>{W`@ihYyc^K!Qp?|He~^81|Tw)~!_xUItbq~0&>o9KRN-^BNee3QOkY`FCOihWbz'
    'I8xk)cN{71BepFm?xS!VDel8NjuiJ1yR8)4RamVQ+vTlRn(ZpAR+{bdZY#xhdD~LdF~xbseka9w`I@FUucD4A&MU5Cx$}zsPRc%L'
    '-$eVszDe%`n=ic&<eO+8$T#sm_}dFNk>)JCn<#e{-c6)9i`br&JB!#&lsk*qo|HR_*mjj$u-JB$Td>%9rC2a;yUHzCY`an{n73W!'
    '7A&?WMW3X(FmIPqTv*X3DK0GTlX4dp_er@6i+d);g?W#YvTtO>Xy3?)>3w70r1y<{6YU%OCfYYLVzh7GIu%YK#WloEA;mR#8&d8X'
    'HgyW+uAy)WDXzggg%sBi+mLeC;4N5+9rG3}&5jioEX|I^7Oc#Uc?*_i$GinAw`1OdrP#69hWI`#cVw|$DtBaYPo_As*e;bhve?&@'
    'JF>VB%N<$VljV*qwl*pItbG&jGx;XH&uq%{K9g^veJ0;T`^>&c?=$-*+UMf-*aeh3f=%s4nInkpM!6%1?MAsHi0wv-BPd)ziX-qY'
    'AjJ{HE+EAbcsrJ2%?dk~V$HlAOR;9&j-^;LZ^u%sS?tKlty%2I%B@*!$5O0WVK-vCRPN3;?fEiy7WaI)JBxe1+?~aJUhdA~K2LFH'
    'MW3g+GjEqt+?n?><#p-FH>tX?Z_;&P-=yopzKQCheG}D%4VtbC8#Jm588lrNf4k4&r{wnI9DaFj-{<gCa{F-(zdW}e=kQZ<`#y)C'
    'lH2z={PNts&*7)!_TwCWd2ZiZvlN@=tyzjq+ti(v*|gZ2mD{w~nw8r$Z_QF{TI|lsZCY&2%57Tg&dP0CY%9EfDR*kIe<^or{&AG%'
    ')cj*A&8ZcSsT8N?A5$q#%|DLHom%W)Qk<IiFXc`x_AljiB;Q1JB;Uk!B;Ta#*ppdPb!6Y9>&U)I*O7b^)sfAbt|R*<s$+4x&%LMQ'
    '<bCcvB_|)}-cxe&KKEXplaF)nDLHwcdoRz)``mj<PCm8|<vID-K9uL=eeOLaCm%bta?2Lmv~tVlZCaXT^G>bYvc)#7+_G(I)5<Jc'
    '?9|FFTkO<QEL&mIQY@RdX=#?Nun+O$wA{7%$7z~ti#<z<YbzeJ<*qHZOXaRDew>!Ow%D_zxHkWoEq874V>ZRLdC!vK+Pr5;sk`<~'
    'RCo4GRChLRy6)OHQQg@$>AI6|qPnwhqPmlB(sgI!rt8kWN!NW-<5uL%%X8^IXP%Zz_cozCmmcTL%X8_mO(@T$`<!`7E<Lsh<+*g9'
    'Gf&B-`<!`7E<Lsh<+*g9Gf&H<7nUu>zHMsR%IurBY-#qbuxu&zEq-jK*f;Om%I%xCY$^85TecMY7F)J*`xd*la{J~jTZ(=2HX-&Y'
    '<qpn252QIb|2&Z5;JjTbcX07@Lb-#BeM*Xh^Unz>4$k|Oat9atlyV0bKPQwsIR8A5;^4ebN$C^vP1Gmsn{=PBiK9Lt-=zD5d=vEv'
    '`zG!aZQ^vFkZ+<sVc$f3qJ0zhiS|v@C$Vq(j9u{je%7$^x`}?>*-^EZ$4$3`o}D`>UhiecKlT~B|M8zi>+HSFw%^((cii=LXUBmy'
    '<n+DmlD3)Ay1o5iyLju*W<RrsUw3v)wLeTh!0!4^<0QY%-bZc!?7{hbvHCiju{G|_srkIEV!glp^06tlbnZP9<MqBaZA3LZUW#?4'
    'QnkO#+|%y5^Uh7yQ|zS$d*^ez>g&#q&vgCGINe5Xec436&hGpCIS1tXP+xa;wA&w>4$o$B?%~&!%7J#&HxJ2PvnKj=d;2u|<4s@e'
    '`nT=Ty0c@N{rbEwWdC-P^&YnM)>G}LUwm<rU$?jKWiP!m)&6tei=uUB#|*o4#X(sPx)QIa*-gU^$$x*bHrs#MUilocVy*34%FM6$'
    '=gFphxEWjg^MyfUL#Lgcw`}a=Qp}y6`4#_8ZO7Qk(QGVoUfPJUBcmBu`uE3njLe;Od2H^q%Zp8%_Hijjk1e4#dOY*1xCXLa?5fCi'
    'k(DFcMXpL4F1CAQxafMwaOvxbXH?OAH0}7v=&|FY`Dohl#k0w@k4rOsWE;u!Y1>Gqk7j<w*H1IEv}59#S=up?y&}iN_DVY@o|8q_'
    'Pjj;9`n9oQhegJUte>}6+Vqk8W79|OPn$k=f7<ks`}1~;eO$Q#<e6XE0Ft$21E{Sf8$dntE546pqqG|$8%1u2Z4|j7vQcE^$VO>5'
    '#0E;=Uouc^1Ia*<4I~4l?=KrDy1#zj6B$5qg4zI*6C?x3PEZ>_c7kL8$q5z~jC@>*8RVH?WCpeUWHYGkCz(OEpV|!a%rCz`+Aguv'
    'q1jB@>5yGwD@QY}$jXsj(oTo%5;+}hlz4w=1`|0ZZIswC(HtwiKWvm}f5<4&{&>4YGvl-?WHYE;A)7&Rg)}oxyF#8BN3M{}pmv4v'
    'tTgT8(u^U^k|SfNEh-s9wy4?|vPIR#kY|38F{GJaeh<kOX&1w`h+GWWBJE;&nw_Lw4A~;Ga@rP=i{Tkn+QqOTqWvU8r1z5z5!pkY'
    'k)-yM4G}pbZHU+z(OfFpPj8FJ7;1+|#*iJNHiqmFc_y85h-3`eA<|4b?GV`*YKItGE$!n{Od`*!(<YH@ESp50Ri{iM&-~IRk!`Ft'
    'iDYBRB+|?;zvpa!$jb4|DdkXj=9G3QJabAr6rMRn4n^A^awuef*viptBkfSw_~`xbY0i{(Ks0BH91zW!qWz~iQ+of&_^?&f#)tQx'
    'W*CtJ^7D*n<{i03Z4${XvPsl#kxim@i)0eXE%N+3?G}0dopy_C63H$4S!~+Jr5HxCx?~v1>XKn3t4oHFt*$nVY<0;nYOBkJk!InM'
    'VWgQ~zD8to$jZ^|A?-fM=8*efo1@(a+Z=KqWOK-U(Ci_ya@yvQ`(T?x?t=^tIUSlYMD@}Jhn)@?9JY<x;E-)3gG08FW(?_ik-=fx'
    'NCt=M<>y9e!${7N3?n(mp62T*=g2elv~%Q{dfGXXVI=3s^YyfIWW%VPBhS~<&M~%B+Q+4sN1pkm%_G@iHjgxGkIkc=wMXWWX6=!A'
    'Bs;9lBhUOI^GGwlw0Y#2UqwyH&XBVpJHu9v><l>znhm6#1=|^N7Bm}(temzpY~^Ssly(+uXSA~*J44Qbj11M6j11S8j0{^yJp)MB'
    'myL|BFV6td^(7<2^`$vby1r~=$U<r(!xqxp8JgdxT_n%!(=L+CBfChN-=|$9&+OAKvZtAS%0=@0KJ6meJd%qf^Qc`UnMZb!-bQI3'
    'mtrKzGP9B7nO|fi^~^7ABzcyfHj-?awUOkRUt}a{=9e~-WSQAW(#$V1k~H%xp8cn1_mGv-wuM~-*%q>LWLvar;2BTaHIQv#D@V3P'
    'y9Tx`+BJ}EA=kh&p0sNq+rqAaX7uQOAj86Tk_-#=0~r?G4?Ne2oQpOrJ@tb&EaY6su#j`nhK2iq<~mV7Xv0GN5Ze}QB*{_sG!sxc'
    'N-~n{D9K1_N6F9U<S1!ApmvmOB(<X?BT0^ujih#zJReXyN-~n<C}R_+eO!vEBwNj<l591ZN}3g@O(ofCGL<~@i%ccW{326HGrzQ{'
    '<e6XERPxL(Z7RuDlc}VcU%qF^#IcprCXR2{CXR2{CXR0>6Gyje6USCgn>fB*n>fB*n>f0iO`N`+OdMM|GI4af?iubY-80lb)HBpS'
    ')HB>a)HAw&sAssZbkDH0)ICG}Lp{U&Lp?)%rF(|^hk8c$PkZ}5cHDnYu^XlxJBb`+ior~?mLGQBAN{;{jvv-+Y9mQzll&%`%@k|N'
    '?owMzHiOz)vPsm|l74?|5B2qv@#O2*#*@vXHlE}?$#|0YWaC+GE!pUiwIp|`ttA^hnwLiol&mFPkG7U{J+ZZ<{UH;o_lHd=&1cjm'
    'lnf)AQ0+r`ZX@|nGNIask_k<-mfFOzwbUk#=iF%%$JSDtIJTB_{bVia`e~jWnLe_X<VO8GJKBG3NO}LYA*KCiL(20XwIL;ws0}H3'
    'QZ}UINog)5c~Wgi$&->HO|h0_(0C4=HfU@u$)IU#$?j5HOEPF=E$RO9yg72FWG%^=YHLaNm#ih<U+?U6eaW11eaW2Cd`U8=y1ryi'
    'slH@R$r!RZC4Z{TDfv^LJ4ybO=1!77C38ytRGZTjYsuz|=EQ09Mb?ttC0R>ym)csA`C@BH=8NXR(f-gpI5KhCTC#~FYpM5#tR?Rc'
    'Sxed<@8D>DB^g!SKWtQW|Bz9o{vo4E{X<5T`-hAwnL%w-$*Yo4C9ldxmAtAps^nF9t|fU@ZB)stl2J{umSn8RTC%YsYpIPDSxYun'
    '+FG)^)Yg)W6<bSftjJpOerjt;`^nal9ILjLw4Y=x*{o@6$!3kLCGDrTX}UkjwDNpRZCa^6*|buBYSYU7sZA^OCz)32Pcp4+0JUi)'
    '-^z0{$+yznO!BQ{TD5QGxtZi!wP_{aN~V>3E1TAGYsv1Ct)((eY%R5EVr!{Q6I)9%O*Cgsn<k#KM(&d4tZCCk){^$WCu^xq8Cgp*'
    'Wn?XB|H)eF{pWdV<X&l>8tp&LQzKL6=c(!bCj(3UPX?CypA0PZKN(o=e{Eo?|JlIm{$~SA^Eb)BYSYJaImyFn14|y33@mwAGO*-f'
    '$-t6_Wdo}{EE`zuVcEcvht&o)#agnv)Yg&=5zj%>hN!1GXvz?=wIoAC){+bnSxa)4GzU!^BC?ijh_tn2^QEmN*Nf(zk@@0zXXIqH'
    'wInA?){>koSxa3no_9u0R$EK1m$zN?_|j&UA79$c(&LNGtbTm;WM=hzPcpMK-;>O&eteOc<;NG9S$ceFGfPH~%q;m?GPC4odor`i'
    '&ytxXKTBqo{4AMS^0RDawVx$3OMaHktoE~PX3MQ5nH`=}M(&d5lxed=)>4}tvX*Ri$Xb%Sq&a2eF3DPIv%}U>n;o80rp*pnOR6u='
    'BcuBAJTh{%+FI)RlC`AzvbEIp<#}XOU$U0EzHBYY)zUmNa<zrMqQ@^8TYCJmvE|1v8C(7M)y9_RhiYR>k6$vj{P-nfOOIb|Z0YgK'
    '#+DwxWNgXYk+Id@mW(ZVTb?UQ-j<B5_O@(nwYMc>OWu}^t@gHTY{}bdV@uwa=ZccI)y6i(TC%&OIbvjF$Xb%S)Yg)W3|mWWWO$Ak'
    'xl6K^+Q^W#BqKxCl8g*nOKoJxTC$PR){^>x=Y^5OC2L9jpsgkK16xZnQ#3D(`$1bvGE>@GvYFD>lKX+ICG~^0medcijiToVZE|@&'
    'DVbdT{J<txKR=MkrRN7Sx%~V<CYPQc$mG)VgEqPR{Gd%PKR;-b%kxRK$z?;QO)mLdGP&e)d2T8BTy1j6=knZA^0{Pkwa+D!OFoxO'
    'F8N$Cx#V-%<Z7QwCYO9Jo7{41$?h^`{-8H>Df0)tp-Y)R=nY-U{6YUS<?{#QpGlcN=nY-U{6TN%%I6RIpGlcN=zk_<{$TtwDf0*Y'
    '&y@Sz*kGpk+~W2$pIh9X=5u}jr1;$8_7tBR8_X1+>u*o-xy9`%J~!^4a-SRDUhZ?_+f#gQaeHhn%b$O!mr@LG+VhX@r4+-P_WYxJ'
    'DaG)nJ^$!lN-?}C&p+HtDTcTF`G<R{-0=Ed^6UQxX&Pv?'
))
PREFLOP = tuple(struct.iter_unpack("<fff", _PREFLOP_BYTES[4:]))
del _PREFLOP_BYTES


"""Per-table tracker. Normal updates consume incremental events exactly once.

The platform advances the feed with returned memory; history is used only for
recovery after corrupt/missing memory. Module state is immutable format data.
"""

import struct
import zlib

_TR_MAGIC = b"KVT1"
_TR_VERSION = 1
_TR_SEATS = 10
_TR_NSTATS = 18
(_TR_HANDS, _TR_VPIP, _TR_PFR, _TR_PRE_N, _TR_PRE_FOLD, _TR_PRE_CALL,
 _TR_PRE_RAISE, _TR_POST_N, _TR_POST_FOLD, _TR_POST_CALL, _TR_POST_RAISE,
 _TR_SHOVE_N, _TR_SHOVE, _TR_DEEP_N, _TR_DEEP_SHOVE, _TR_EXP_N,
 _TR_EXP_LOW, _TR_ALLIN_RAISES) = range(_TR_NSTATS)
_TR_FORMAT = struct.Struct("<4sBBIBBQ5H4I10Q10Q10B180H")
_TR_CRC = struct.Struct("<I")
_TR_SIZE = _TR_FORMAT.size + _TR_CRC.size
_TR_RANKS = "23456789TJQKA"
_TR_SUITS = "cdhs"


def _tr_card(card):
    if len(card) != 2:
        return 255
    rank, suit = _TR_RANKS.find(card[0]), _TR_SUITS.find(card[1])
    return rank * 4 + suit if rank >= 0 and suit >= 0 else 255


def _tr_table_signature(state):
    return zlib.crc32(str(state.config.table_id).encode("utf-8")) & 0xFFFFFFFF


def _tr_new_record(state, resets=0):
    players = min(_TR_SEATS, max(0, int(state.config.players)))
    from_start = bool(state.events and state.events[0].kind == "hand"
                      and state.events[0].amount == 1)
    return {
        "players": players, "hand": 0, "street": 0, "board_count": 0,
        "bb": max(1, int(state.blinds.big_blind)),
        "vpip_mask": 0, "pfr_mask": 0, "shove_opp_mask": 0,
        "deep_opp_mask": 0, "shown_mask": 0,
        "internal_errors": 0, "deadline_fallbacks": 0,
        "memory_resets": resets, "table_signature": _tr_table_signature(state),
        "remaining": [int(state.config.starting_stack) if i < players else 0
                      for i in range(_TR_SEATS)],
        "bets": [0] * _TR_SEATS, "exposed": [255] * _TR_SEATS,
        "stats": [[0] * _TR_NSTATS for _ in range(_TR_SEATS)],
        "_rebuild": not from_start,
    }


def load_record(memory, state):
    """Decode a CRC record; malformed or truncated bytes start afresh."""
    try:
        if len(memory) != _TR_SIZE:
            raise ValueError("record length")
        body = memory[:-4]
        if zlib.crc32(body) & 0xFFFFFFFF != _TR_CRC.unpack(memory[-4:])[0]:
            raise ValueError("record checksum")
        v = _TR_FORMAT.unpack(body)
        players = min(_TR_SEATS, max(0, int(state.config.players)))
        if (v[0] != _TR_MAGIC or v[1] != _TR_VERSION or v[2] != players
                or v[3] > state.hand_number or v[4] > 3
                or v[5] not in (0, 3, 4, 5) or not v[6]
                or v[15] != _tr_table_signature(state)):
            raise ValueError("record header")
        return {
            "players": v[2], "hand": v[3], "street": v[4],
            "board_count": v[5], "bb": v[6], "vpip_mask": v[7],
            "pfr_mask": v[8], "shove_opp_mask": v[9],
            "deep_opp_mask": v[10], "shown_mask": v[11],
            "internal_errors": v[12], "deadline_fallbacks": v[13],
            "memory_resets": v[14], "table_signature": v[15],
            "remaining": list(v[16:26]), "bets": list(v[26:36]),
            "exposed": list(v[36:46]),
            "stats": [list(v[46 + i * _TR_NSTATS:46 + (i + 1) * _TR_NSTATS])
                      for i in range(_TR_SEATS)],
            "_rebuild": False,
        }
    except (ValueError, TypeError, OverflowError, struct.error):
        first = (not memory and state.events and state.events[0].kind == "hand"
                 and state.events[0].amount == 1)
        return _tr_new_record(state, 0 if first else 1)


def _tr_increment(row, index):
    if row[index] < 65535:
        row[index] += 1


def _tr_start_hand(rec, number, state):
    rec["hand"] = number
    rec["street"] = rec["board_count"] = 0
    rec["vpip_mask"] = rec["pfr_mask"] = 0
    rec["shove_opp_mask"] = rec["deep_opp_mask"] = rec["shown_mask"] = 0
    rec["bets"] = [0] * _TR_SEATS
    rec["exposed"] = [255] * _TR_SEATS
    levels = state.config.blinds
    if levels:
        index = min(len(levels) - 1, max(0, number - 1)
                    // max(1, state.config.hands_per_level))
        rec["bb"] = max(1, levels[index].big_blind)
    for seat in range(rec["players"]):
        if rec["remaining"][seat] > 0:
            _tr_increment(rec["stats"][seat], _TR_HANDS)


def _tr_apply_events(rec, events, state):
    remaining, bets, stats = rec["remaining"], rec["bets"], rec["stats"]
    max_bet = max(bets)
    for event in events:
        kind = event.kind
        if kind == "hand":
            _tr_start_hand(rec, event.amount, state)
            bets = rec["bets"]
            max_bet = 0
            continue
        if kind == "board":
            rec["board_count"] = min(5, rec["board_count"] + len(event.cards))
            rec["street"] = max(1, rec["board_count"] - 2)
            bets = rec["bets"] = [0] * _TR_SEATS
            max_bet = 0
            continue
        seat = event.seat
        if seat is None or not 0 <= seat < rec["players"]:
            continue
        row = stats[seat]
        if kind == "stack":
            remaining[seat] = max(0, event.amount)
            bets[seat] = 0
            continue
        if kind == "ante":
            remaining[seat] = max(0, remaining[seat] - event.amount)
            continue
        if kind == "blind":
            remaining[seat] = max(0, remaining[seat] - event.amount)
            bets[seat] += event.amount
            max_bet = max(max_bet, bets[seat])
            continue
        if kind == "reveal":
            if event.cards:
                rec["exposed"][seat] = _tr_card(event.cards[0])
            continue
        if kind == "show":
            bit = 1 << seat
            if len(event.cards) == 2 and not rec["shown_mask"] & bit:
                rec["shown_mask"] |= bit
                exposed = rec["exposed"][seat]
                a, b = _tr_card(event.cards[0]), _tr_card(event.cards[1])
                hidden = b if a == exposed else a if b == exposed else 255
                if exposed != 255 and hidden != 255 and exposed // 4 != hidden // 4:
                    _tr_increment(row, _TR_EXP_N)
                    if exposed // 4 < hidden // 4:
                        _tr_increment(row, _TR_EXP_LOW)
            continue
        if kind not in ("fold", "check", "call", "raise"):
            continue

        bit = 1 << seat
        preflop = rec["street"] == 0
        before = remaining[seat]
        owed = max(0, max_bet - bets[seat])
        if preflop:
            # Count a hand once when the player has chips above the call price.
            if before > owed:
                if not rec["shove_opp_mask"] & bit:
                    rec["shove_opp_mask"] |= bit
                    _tr_increment(row, _TR_SHOVE_N)
                if before + bets[seat] > 15 * rec["bb"] and not rec["deep_opp_mask"] & bit:
                    rec["deep_opp_mask"] |= bit
                    _tr_increment(row, _TR_DEEP_N)
            if kind in ("call", "raise") and not rec["vpip_mask"] & bit:
                rec["vpip_mask"] |= bit
                _tr_increment(row, _TR_VPIP)
            if kind == "raise" and not rec["pfr_mask"] & bit:
                rec["pfr_mask"] |= bit
                _tr_increment(row, _TR_PFR)

        if owed > 0 and before > 0 and kind != "check":
            base = _TR_PRE_N if preflop else _TR_POST_N
            _tr_increment(row, base)
            _tr_increment(row, base + (1 if kind == "fold" else 2 if kind == "call" else 3))

        if kind == "call":
            remaining[seat] = max(0, before - event.amount)
            bets[seat] += event.amount
        elif kind == "raise":
            delta = max(0, event.amount - bets[seat])
            if before > 0 and delta >= before:
                _tr_increment(row, _TR_ALLIN_RAISES)
                if preflop and row[_TR_SHOVE_N]:
                    _tr_increment(row, _TR_SHOVE)
                    if before + bets[seat] > 15 * rec["bb"] and row[_TR_DEEP_N]:
                        _tr_increment(row, _TR_DEEP_SHOVE)
            remaining[seat] = max(0, before - delta)
            bets[seat] = event.amount
            max_bet = max(max_bet, event.amount)


def _tr_rebuild_current(rec, state):
    """Recover current context, discarding unknown earlier-hand statistics.

    Contributions plus live stacks reconstruct normal starting stacks. A hidden
    uncalled refund can overestimate them, so recovered shove data is discarded.
    """
    spent, bets = [0] * _TR_SEATS, [0] * _TR_SEATS
    for event in state.history:
        if event.kind == "board":
            bets = [0] * _TR_SEATS
            continue
        seat = event.seat
        if seat is None or not 0 <= seat < rec["players"]:
            continue
        if event.kind == "ante":
            spent[seat] += event.amount
        elif event.kind in ("blind", "call"):
            spent[seat] += event.amount
            bets[seat] += event.amount
        elif event.kind == "raise":
            spent[seat] += max(0, event.amount - bets[seat])
            bets[seat] = event.amount
    for seat in state.seats:
        if 0 <= seat.seat < rec["players"]:
            rec["remaining"][seat.seat] = seat.stack + spent[seat.seat]
    _tr_start_hand(rec, state.hand_number, state)
    _tr_apply_events(rec, state.history, state)
    for row in rec["stats"]:
        row[_TR_SHOVE_N] = row[_TR_SHOVE] = 0
        row[_TR_DEEP_N] = row[_TR_DEEP_SHOVE] = row[_TR_ALLIN_RAISES] = 0
    # Suppress partial-hand denominators; zero denominators suppress successes.
    rec["shove_opp_mask"] = rec["deep_opp_mask"] = (1 << rec["players"]) - 1
    rec["_rebuild"] = False


def feed_record(rec, state):
    """Apply the incremental feed, then reconcile chip state to the live view."""
    if rec.get("_rebuild", False):
        _tr_rebuild_current(rec, state)
    else:
        _tr_apply_events(rec, state.events, state)
    # This view includes uncalled refunds not separately logged as public events.
    for seat in state.seats:
        if 0 <= seat.seat < rec["players"]:
            rec["remaining"][seat.seat] = max(0, seat.stack)
            rec["bets"][seat.seat] = max(0, seat.bet)
            if len(seat.shown_cards) == 1:
                rec["exposed"][seat.seat] = _tr_card(seat.shown_cards[0])
    rec["board_count"] = len(state.board)
    rec["street"] = max(0, len(state.board) - 2)


def dump_record(rec, state):
    """Encode below 1 KB. Undersized configured memory gets a clean reset."""
    if state.config.memory_bytes < _TR_SIZE:
        return b""
    flat = [value for row in rec["stats"] for value in row]
    body = _TR_FORMAT.pack(
        _TR_MAGIC, _TR_VERSION, rec["players"], rec["hand"], rec["street"],
        rec["board_count"], rec["bb"], rec["vpip_mask"], rec["pfr_mask"],
        rec["shove_opp_mask"], rec["deep_opp_mask"], rec["shown_mask"],
        min(0xFFFFFFFF, max(0, rec["internal_errors"])),
        min(0xFFFFFFFF, max(0, rec["deadline_fallbacks"])),
        min(0xFFFFFFFF, max(0, rec["memory_resets"])), rec["table_signature"],
        *rec["remaining"], *rec["bets"], *rec["exposed"], *flat,
    )
    return body + _TR_CRC.pack(zlib.crc32(body) & 0xFFFFFFFF)


def opponent_rates(rec, seat):
    """Return continuous priors and sample counts, not opponent labels.

    Facing-bet rates share a denominator and sum to one. Exposure evidence is
    conditional on showdowns and should only weakly tilt hidden-card beliefs.
    Shove rates cover preflop; allin_raises additionally counts later streets.
    """
    row = rec["stats"][seat] if 0 <= seat < rec["players"] else (0,) * _TR_NSTATS
    hands, pre, post = row[_TR_HANDS], row[_TR_PRE_N], row[_TR_POST_N]
    shove, deep, exposed = row[_TR_SHOVE_N], row[_TR_DEEP_N], row[_TR_EXP_N]
    result = {
        "hands": hands,
        "vpip": (row[_TR_VPIP] + 0.30 * 16) / (hands + 16),
        "pfr": (row[_TR_PFR] + 0.18 * 16) / (hands + 16),
        "fold_pre": (row[_TR_PRE_FOLD] + 0.46 * 20) / (pre + 20),
        "call_pre": (row[_TR_PRE_CALL] + 0.43 * 20) / (pre + 20),
        "raise_pre": (row[_TR_PRE_RAISE] + 0.11 * 20) / (pre + 20),
        "fold_post": (row[_TR_POST_FOLD] + 0.38 * 20) / (post + 20),
        "call_post": (row[_TR_POST_CALL] + 0.48 * 20) / (post + 20),
        "raise_post": (row[_TR_POST_RAISE] + 0.14 * 20) / (post + 20),
        "shove": min(1.0, (row[_TR_SHOVE] + 0.06 * 24) / (shove + 24)),
        "deep_shove": min(1.0, (row[_TR_DEEP_SHOVE] + 0.015 * 32) / (deep + 32)),
        "exposure_low": (row[_TR_EXP_LOW] + 12) / (exposed + 24),
        "pre_opportunities": pre, "post_opportunities": post,
        "shoves": row[_TR_SHOVE], "deep_shoves": row[_TR_DEEP_SHOVE],
        "allin_raises": row[_TR_ALLIN_RAISES],
        "confidence": hands / (hands + 16),
    }
    for key, count, weight in (("vpip", hands, 16), ("pfr", hands, 16),
                               ("fold_pre", pre, 20), ("call_pre", pre, 20),
                               ("raise_pre", pre, 20), ("fold_post", post, 20),
                               ("call_post", post, 20), ("raise_post", post, 20),
                               ("shove", shove, 24), ("deep_shove", deep, 32),
                               ("exposure_low", exposed, 24)):
        result[key + "_n"] = count
        result[key + "_confidence"] = count / (count + weight)
    return result


"""Pot accounting and conservative isolated-all-in tournament utilities.

Helpers use public state only. ICM values survivor continuation; it is not a
solution to future betting. The scalar call threshold compares decisive win and
loss branches, so applying it to equity that includes ties is an approximation.
"""

from poker_agent_sdk import icm


def _hand_contributions(state):
    """Return per-seat paid chips, or None if the public ledger is incomplete.

    Calls/blinds/antes are increments; raises are street totals. The simulator
    does not emit uncalled-refund events, so reject any unmatched ledger rather
    than silently treating refunded chips as part of a pot.
    """
    seats = state.seats
    if not seats:
        return None
    size = max(s.seat for s in seats) + 1
    paid = [0] * size
    bets = [0] * size
    for event in state.history:
        kind = event.kind
        if kind == 'board':
            bets = [0] * size
            continue
        if kind in ('win', 'stack'):
            return None
        seat = event.seat
        if kind not in ('ante', 'blind', 'call', 'raise'):
            continue
        if seat is None or not 0 <= seat < size or event.amount < 0:
            return None
        amount = event.amount
        if kind == 'ante':
            paid[seat] += amount
        elif kind == 'raise':
            if amount < bets[seat]:
                return None
            paid[seat] += amount - bets[seat]
            bets[seat] = amount
        else:
            paid[seat] += amount
            bets[seat] += amount
    if sum(paid) != state.pot or any(bets[s.seat] != s.bet for s in seats):
        return None
    return paid


def callable_pot(state, me):
    """Current pot hero can win after calling, excluding the new call chips.

    Include folded players' dead money, capped separately at hero's total hand
    contribution after the call. Incomplete synthetic/unsupported histories use
    a current-street-only correction; such states cannot use the ICM shortcut.
    """
    cost = min(max(0, state.to_call), max(0, me.stack))
    paid = _hand_contributions(state)
    if paid is not None:
        cap = paid[me.seat] + cost
        return sum(min(amount, cap) for amount in paid)
    cap = me.bet + cost
    excess = sum(max(0, seat.bet - cap) for seat in state.seats)
    return max(0, state.pot - excess)


def _hero_icm(stacks, payouts, hero):
    """Same survivor ICM as the SDK, optimized for up to three paid places."""
    if stacks[hero] <= 0 or not payouts:
        return 0.0
    if len(payouts) > 3:
        return icm(stacks, payouts)[hero]
    chips = stacks[hero]
    others = [stack for seat, stack in enumerate(stacks) if seat != hero and stack > 0]
    total = chips + sum(others)
    value = payouts[0] * chips / total
    if len(payouts) > 1:
        for first, a in enumerate(others):
            first_probability = a / total
            after_first = total - a
            value += payouts[1] * first_probability * chips / after_first
            if len(payouts) > 2:
                for second, b in enumerate(others):
                    if second != first:
                        value += (payouts[2] * first_probability * b / after_first
                                  * chips / (after_first - b))
    return value


def icm_call_threshold(state, me, opponent, cost, pot):
    """Binary showdown-equity threshold for a supported isolated all-in call.

    Return None for a multiway contest, incomplete accounting, or a call that
    leaves future betting. Returned values already contain ICM risk adjustment:
    do not add another risk premium or floor them at the chip-EV price.

    ``pot`` must be callable_pot(state, me). Folded dead money and unequal stacks
    are supported. Every uncontested side layer goes to its eligible survivor;
    uncalled excess therefore never masquerades as chips hero could win.
    """
    hero, villain = me.seat, opponent.seat
    if hero != state.seat or hero == villain or cost <= 0:
        return None
    if cost != min(state.to_call, me.stack):
        return None
    live = [s for s in state.seats if s.status in ('active', 'all_in')]
    if len(live) != 2 or {s.seat for s in live} != {hero, villain}:
        return None
    if cost != me.stack and opponent.stack != 0:
        return None
    # A previously folded zero-stack player would introduce simultaneous bust
    # ordering that cannot be inferred safely from this narrow two-player model.
    if any(s.status == 'folded' and s.stack == 0 for s in state.seats):
        return None
    paid = _hand_contributions(state)
    if paid is None:
        return None
    hero_total = paid[hero] + cost
    if pot != sum(min(amount, hero_total) for amount in paid):
        return None
    called = paid.copy()
    called[hero] = hero_total
    villain_total = called[villain]
    upper = max(hero_total, villain_total)
    if any(amount > upper for seat, amount in enumerate(called)
           if seat not in (hero, villain)):
        return None  # A pot layer has no live eligible player.
    # The opponent must be able to collect every current layer when hero folds.
    if any(amount > paid[villain] for amount in paid):
        return None
    main_cap = min(hero_total, villain_total)
    contested = sum(min(amount, main_cap) for amount in called)
    side = sum(called) - contested
    hero_side = side if hero_total > villain_total else 0
    villain_side = side if villain_total > hero_total else 0
    if not contested:
        return None

    stacks = [0] * len(paid)
    for seat in state.seats:
        stacks[seat.seat] = seat.stack
    folded = stacks.copy()
    folded[villain] += state.pot
    won = stacks.copy()
    won[hero] += contested + hero_side - cost
    won[villain] += villain_side
    lost = stacks.copy()
    lost[hero] += hero_side - cost
    lost[villain] += contested + villain_side
    payouts = state.config.payouts
    vf = _hero_icm(folded, payouts, hero)
    vw = _hero_icm(won, payouts, hero)
    if lost[hero] == 0:
        # The SDK assigns zero to busted stacks; award the earned place first.
        place = sum(stack > 0 for stack in lost)
        vl = payouts[place] if place < len(payouts) else 0.0
    else:
        vl = _hero_icm(lost, payouts, hero)
    spread = vw - vl
    if spread <= 1e-12:
        return 0.0 if vf <= vl + 1e-12 else 1.0
    return max(0.0, min(1.0, (vf - vl) / spread))


def fallback(state):
    for kind in ('check', 'fold', 'call'):
        if state.can(kind):
            return Action(kind)
    first = state.legal_actions[0]
    return Action(first.kind, first.min_amount)


def raise_to(state, amount):
    legal = state.can('raise')
    if legal:
        return Action.raise_to(max(legal.min_amount, min(legal.max_amount, int(amount))))
    return Action.call() if state.can('call') else fallback(state)


def pair_strength(a, b):
    """Smooth preflop ordering only, not a claim of measured equity."""
    x, y = sorted((a // 4 + 2, b // 4 + 2), reverse=True)
    if x == y:
        return .50 + .027 * (x - 2)
    value = .30 + .024 * (x - 2) + .012 * (y - 2)
    value += .025 if a % 4 == b % 4 else 0
    value += .022 if x - y == 1 else .010 if x - y == 2 else 0
    value -= .025 if x - y > 5 and x < 14 else 0
    return value


def pre_strength(hole):
    scores = sorted((pair_strength(hole[i], hole[j]) for i, j in itertools.combinations(range(len(hole)), 2)), reverse=True)
    if len(scores) == 1:
        return scores[0]
    # The third card provides an option after seeing the flop, not a third showdown card.
    return scores[0] + .10 * max(0, scores[1] - .44)


def flop_quality(hole, board):
    cards = hole + board
    rank = EVAL([CARDS[c] for c in cards])
    category = rank >> 24
    suits = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        suits[c % 4] += 1
        mask |= 1 << (c // 4)
    flush_draw = max(suits) == 4 and any(suits[c % 4] == 4 for c in hole)
    straight_draw = 0
    for high in range(4, 13):
        straight_draw = max(straight_draw, ((mask >> (high - 4)) & 31).bit_count())
    straight_draw = max(straight_draw, (mask & ((1 << 12) | 15)).bit_count())
    # Category dominates ordinary high cards; strong draws can outrank a weak pair.
    value = category * 1.0 + ((rank & 0xffffff) / 0x1000000) * .3
    if category < 4:
        value += .82 if flush_draw else 0
        value += .38 if straight_draw >= 4 else 0
    top = max(c // 4 for c in board)
    value += .08 * sum(c // 4 > top for c in hole)
    return value


def known_cards(state):
    known = {INDEX[c] for c in state.cards + state.board}
    known.update(INDEX[c] for c in state.variant.get('discarded', ()))
    for seat in state.seats:
        known.update(INDEX[c] for c in seat.shown_cards)
    return known


def decision_rng(state, purpose=0):
    # Private cards participate in mixing; no shared generator or public schedule.
    seed = zlib.crc32((''.join(state.cards + state.board)).encode())
    seed ^= zlib.crc32(state.config.table_id.encode())
    seed ^= state.hand_number * 1000003 + state.seat * 7919 + purpose * 104729
    return random.Random(seed)


def choose_cards(state, rec=None, deadline=None):
    if len(state.cards) != 3:
        return Action('select', cards=(2, 0))
    hole = [INDEX[c] for c in state.cards]
    board = [INDEX[c] for c in state.board]
    quality = [flop_quality([hole[i], hole[j]], board) for i, j in PAIRS]
    best = max(range(3), key=lambda i: quality[i])
    if True:
        # Common runouts compare all three retained pairs on identical deals.
        # Opponents choose using the flop only; never let them see the runout.
        known = known_cards(state)
        deck = [c for c in range(52) if c not in known]
        rng = decision_rng(state, 1)
        pairs = [[CARDS[hole[i]], CARDS[hole[j]]] for i,j in PAIRS]
        flop = [CARDS[c] for c in board]
        opponents = sum(s.seat != state.seat and s.status in ('active','all_in') for s in state.seats)
        scores = [0.0]*3
        trials = 24 if opponents <= 2 else 16 if opponents <= 4 else 12
        completed = 0
        for trial in range(trials):
            if deadline is not None and perf_counter_ns() >= deadline:
                break
            deal = rng.sample(deck, 2+3*opponents)
            full = flop + [CARDS[c] for c in deal[:2]]
            rival = -1
            rival_ties = 0
            for seat in range(opponents):
                triple = [CARDS[c] for c in deal[2+3*seat:5+3*seat]]
                held = max(([triple[a],triple[b]] for a,b in PAIRS), key=lambda p:EVAL(p+flop))
                rank = EVAL(held+full)
                if rank>rival: rival,rival_ties=rank,1
                elif rank==rival: rival_ties+=1
            for k,pair in enumerate(pairs):
                rank=EVAL(pair+full)
                scores[k]+=1 if rank>rival else 1/(rival_ties+1) if rank==rival else 0
            completed += 1
        if completed:
            best=max(range(3),key=lambda k:scores[k]+.10*quality[k])
        elif rec is not None:
            rec['deadline_fallbacks'] += 1
    i, j = PAIRS[best]
    discard = 3 - i - j
    # Random exposure removes an ordering tell, not information from retention itself.
    reveal = (i, j)[rng.randrange(2)]
    return Action('select', cards=(discard, reveal))


def risk_margin(state, me, cost, opponents):
    if state.players_remaining <= 2:
        return 0.0
    paid = sum(p > 0 for p in state.config.payouts)
    payout_total = max(1, sum(state.config.payouts))
    flatness = 1 - state.config.payouts[0] / payout_total
    fraction = cost / max(1, me.stack)
    margin = .035 * flatness * min(1, fraction * 2)
    if state.players_remaining == paid + 1 and fraction > .5:
        smaller = sum(0 < s.stack < me.stack * .6 for s in state.seats if s.seat != me.seat)
        margin += .055 + .025 * min(2, smaller)
    return margin


def _action_context(state):
    """Last postflop action and the board length available when it occurred."""
    board_count = 0
    actions = {}
    checks = 0
    for event in state.history:
        if event.kind == 'board':
            board_count += len(event.cards)
            checks = 0
        elif board_count and event.kind in ('raise', 'call', 'check'):
            actions[event.seat] = (event.kind, board_count)
            checks += event.kind == 'check'
    return actions, checks


def _range_rows(state, opponents, deck, rec):
    """Conservative retention/action hypotheses, not a calibrated posterior."""
    actions, _ = _action_context(state)
    flop = [CARDS[INDEX[c]] for c in state.board[:3]]
    suits = [sum(INDEX[c] % 4 == s for c in state.board[:3]) for s in range(4)]
    rows = []
    for seat in opponents:
        if len(seat.shown_cards) != 1:
            rows.append(None)
            continue
        exposed = INDEX[seat.shown_cards[0]]
        rates = opponent_rates(rec, seat.seat) if rec is not None else {}
        low = rates.get('exposure_low', .5)
        aggression = rates.get('raise_post', .20)
        action, street = actions.get(seat.seat, ('none', 3))
        action_board = [CARDS[INDEX[c]] for c in state.board[:street]]
        weights = {}
        for hidden in deck:
            pair = [CARDS[exposed], CARDS[hidden]]
            category = EVAL(pair + flop) >> 24
            draw = suits[hidden % 4] + (exposed % 4 == hidden % 4) == 3
            weight = 1.0 + .18 * min(category, 3) + .10 * draw
            if hidden // 4 != exposed // 4:
                direction = 1 if hidden // 4 > exposed // 4 else -1
                weight *= 1.0 + direction * (low - .5)
            if action in ('raise', 'call'):
                current = EVAL(pair + action_board) >> 24
                if action == 'raise':
                    shape = (.30, .80, 1.45, 1.65, 1.8, 1.8, 1.9, 1.9, 1.9)[current]
                    mix = max(.15, min(.65, .72 - aggression))
                else:
                    shape = (.55, 1.05, 1.25, 1.30, 1.35, 1.35, 1.4, 1.4, 1.4)[current]
                    mix = .35
                weight *= 1.0 + mix * (shape - 1.0)
            weights[hidden] = weight
        rows.append(weights)
    return rows


def equity(state, opponents, rec=None, deadline=None):
    """Joint pot share with without-replacement cards and correctly split ties.

    On a heads-up river, enumerate every legal hidden card with soft range weights.
    Else draw complete joint deals and importance-weight those same hypotheses.
    """
    known = known_cards(state)
    deck = [c for c in range(52) if c not in known]
    shown = [[INDEX[c] for c in s.shown_cards] for s in opponents]
    rows = _range_rows(state, opponents, deck, rec)
    board = [CARDS[INDEX[c]] for c in state.board]
    hero = [CARDS[INDEX[c]] for c in state.cards]
    missing = 5 - len(board)
    if not missing and len(opponents) == 1 and len(shown[0]) == 1:
        mine = EVAL(hero + board)
        won = total = 0.0
        for hidden in deck:
            rank = EVAL([CARDS[shown[0][0]], CARDS[hidden]] + board)
            weight = rows[0][hidden]
            won += weight * (1 if mine > rank else .5 if mine == rank else 0)
            total += weight
        return won / total if total else .5
    rng = decision_rng(state, 2)
    samples = 36 if len(opponents) <= 2 else 24
    needed = missing + sum(max(0, 2 - len(x)) for x in shown)
    total = won = 0.0
    for _ in range(samples):
        if total and deadline is not None and perf_counter_ns() >= deadline:
            break
        deal = rng.sample(deck, needed)
        full = board + [CARDS[c] for c in deal[:missing]]
        mine = EVAL(hero + full)
        best, ties, offset, weight = mine, 1, missing, 1.0
        for j, exposed in enumerate(shown):
            n = max(0, 2 - len(exposed))
            hidden = deal[offset:offset+n]
            offset += n
            if rows[j] is not None:
                weight *= rows[j][hidden[0]]
            rank = EVAL([CARDS[c] for c in exposed + hidden] + full)
            if rank > best:
                best, ties = rank, 1
            elif rank == best:
                ties += 1
        total += weight
        if mine == best:
            won += weight / ties
    return won / total if total else 0.0


def _pre_multiway(state, opponents, mixes, deadline):
    """Joint preflop rollout; every simulated discard is locked on the flop."""
    hole = [INDEX[c] for c in state.cards]
    deck = [c for c in range(52) if c not in hole]
    rng = decision_rng(state, 3)
    won = total = 0.0
    def keep(triple, flop):
        return max(([triple[a], triple[b]] for a, b in PAIRS), key=lambda p: EVAL(p + flop))
    for _ in range(24):
        if total and deadline is not None and perf_counter_ns() >= deadline:
            break
        dealt = rng.sample(deck, 5 + 3 * len(opponents))
        board = [CARDS[c] for c in dealt[:5]]
        mine = EVAL(keep([CARDS[c] for c in hole], board[:3]) + board)
        best, ties, weight = mine, 1, 1.0
        for i in range(len(opponents)):
            triple = dealt[5+3*i:8+3*i]
            tight = pre_strength(triple) >= .67
            weight *= mixes[i] + (1.0 - mixes[i]) * (1.0 if tight else .08)
            rank = EVAL(keep([CARDS[c] for c in triple], board[:3]) + board)
            if rank > best:
                best, ties = rank, 1
            elif rank == best:
                ties += 1
        total += weight
        if mine == best:
            won += weight / ties
    return won / total if total else 0.0


def _range_mix(rates, depth):
    mix = max(.05, min(1.0, (rates['pfr'] - .16) / .35))
    if depth <= 4:
        mix = max(mix, .65)
    elif depth <= 8:
        mix = max(mix, .35)
    return mix


def decide(state, rec, deadline=None):
    if state.phase == 'select':
        return choose_cards(state, rec, deadline)
    if state.phase != 'betting':
        return fallback(state)
    me = next(s for s in state.seats if s.seat == state.seat)
    opponents = [s for s in state.seats if s.seat != state.seat and s.status in ('active', 'all_in')]
    if not opponents:
        return fallback(state)
    call = min(state.to_call, me.stack)
    bb = max(1, state.blinds.big_blind)
    effective = min(me.stack + me.bet, max(s.stack + s.bet for s in opponents))
    eff_bb = effective / bb
    # Discount uncallable excess in a covering opponent's current wager.
    pot = max(1, callable_pot(state, me))
    price = call / (pot + call)
    margin = risk_margin(state, me, call, opponents)
    if call and len(opponents)==1 and (call==me.stack or opponents[0].stack==0):
        threshold=icm_call_threshold(state,me,opponents[0],call,pot)
        if threshold is not None:
            price,margin=threshold,0
    rates={s.seat:opponent_rates(rec,s.seat) for s in opponents}
    if not state.board:
        hole = [INDEX[c] for c in state.cards]
        strength = pre_strength(hole)
        lookup = None
        if len(hole)==3 and PREFLOP:
            a,b,c=sorted(hole)
            lookup=PREFLOP[c*(c-1)*(c-2)//6+b*(b-1)//2+a]
        live = sorted(s.seat for s in state.seats if s.status != 'busted')
        after_button = sorted(live, key=lambda s: (s - state.button - 1) % state.config.players)
        sb, big = (state.button, after_button[0]) if len(live) == 2 else after_button[:2]
        if me.seat == state.button: position = 'btn'
        elif me.seat == sb: position = 'sb'
        elif me.seat == big: position = 'bb'
        else:
            before = sorted(live, key=lambda s: (state.button - s) % state.config.players)
            position = 'co' if before.index(me.seat) == 1 else 'early'
        raises = [e for e in state.history if e.kind == 'raise']
        shovers = [s for s in opponents if rates[s.seat]['pfr'] > .50]
        if not raises:
            cutoff = {'btn':.56, 'sb':.56, 'co':.59, 'early':.63, 'bb':.58}[position]
            if len(live) <= 3: cutoff -= .035
            if shovers: cutoff += .04
            open_hand = strength >= cutoff
            if lookup:
                width={'btn':.48,'sb':.45,'co':.31,'early':.20,'bb':.30}[position]
                if len(live)<=3:width+=.12
                fold_rate=sum(rates[s.seat]['fold_pre'] for s in opponents)/len(opponents)
                width*=max(.85,min(1.25,1+.7*(fold_rate-.60)))
                if shovers:width*=.75
                open_hand=lookup[2]<=width
            if open_hand:
                if eff_bb <= 9:
                    return raise_to(state, me.bet + me.stack)
                limpers = sum(e.kind == 'call' for e in state.history)
                return raise_to(state, bb * (2.2 + .7 * limpers))
            return fallback(state)
        aggressor = raises[-1].seat
        mix=_range_mix(rates.get(aggressor,opponent_rates(rec,aggressor)),eff_bb)
        wide = mix > .6
        heavy = call >= .30 * max(1, me.stack) or max(s.bet for s in opponents) >= 8 * bb
        if heavy:
            # Three-card random opposition is stronger than two random cards.
            # This smooth fallback will be evaluated against actual variant bots.
            e = mix*lookup[0]+(1-mix)*lookup[1] if lookup else max(.05,min(.9,strength-.20+.08*mix))
            committed=[s for s in opponents if s.bet>=max(bb,me.bet+call) or s.status=='all_in']
            if len(committed)>1:
                mixes=[_range_mix(rates[s.seat],min(me.stack+me.bet,s.stack+s.bet)/bb) for s in committed]
                e=_pre_multiway(state,committed,mixes,deadline)
            if e > price + margin + .035:
                return Action.call() if state.can('call') else fallback(state)
            return fallback(state)
        if strength >= .76 and state.can('raise'):
            return raise_to(state, me.bet + me.stack if eff_bb <= 18 else 3 * max(s.bet for s in opponents))
        required = .60 if position == 'bb' else .64
        if len(live) <= 3: required -= .04
        required -= .035*mix
        if strength >= required and call <= .20 * me.stack and price < .38:
            return Action.call() if state.can('call') else fallback(state)
        return fallback(state)
    e = equity(state, opponents, rec, deadline)
    if not call:
        fold_rate=sum(rates[s.seat]['fold_post'] for s in opponents)/len(opponents)
        station=fold_rate<.30
        threshold = .59 if len(opponents) == 1 else .55 if len(opponents) == 2 else .50
        if station:threshold-=.025
        if e >= threshold:
            size = .75 if station and e>=.70 else .65 if e >= .74 else .40
            return raise_to(state, me.bet + max(bb, int(pot * size)))
        # Small, infrequent probes only in heads-up pots after the opponent checks.
        _,checks=_action_context(state)
        if len(opponents)==1 and checks and .25<e<threshold and fold_rate>.56:
            bet=max(bb,pot//3)
            called_equity=max(0,e-.12)
            ev=fold_rate*pot+(1-fold_rate)*(called_equity*(pot+2*bet)-bet)
            if ev>e*pot+.05*pot and decision_rng(state,4).random()<.35:
                return raise_to(state,me.bet+bet)
        return fallback(state)
    if e >= max(.82, price + margin + .28) and state.can('raise'):
        return raise_to(state, me.bet + call + max(bb, int((pot + call) * .8)))
    # Additional margin controls small-sample equity uncertainty and multiway
    # range selection; do not use raw sampled equity as an exact probability.
    uncertainty=.045 if len(state.board)<5 or len(opponents)>1 else .025
    if e >= price + margin + uncertainty:
        return Action.call() if state.can('call') else fallback(state)
    return fallback(state)


class Agent(BaseAgent):
    def act(self, state, memory):
        deadline=perf_counter_ns()+BUDGET_NS
        rec=load_record(memory,state)
        try:
            feed_record(rec,state)
            action=decide(state,rec,deadline)
            legal=state.can(action.kind)
            if legal is None or (action.kind=='raise' and not legal.min_amount<=action.amount<=legal.max_amount):
                raise ValueError('illegal proposed action')
        except Exception:
            rec['internal_errors']+=1
            action=fallback(state)
        try:
            packed=dump_record(rec,state)
        except Exception:
            clean=load_record(b'',state)
            clean['internal_errors']=rec.get('internal_errors',0)+1
            packed=dump_record(clean,state)
        return action,packed


# Eager immutable evaluator warm-up; no process-wide GC mutation.
EVAL(list(CARDS[:7]))


