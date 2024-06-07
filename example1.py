from AttackT_Struct import *


# comment
# IRID =

Insert_rem=Leaf("IRID",10,100)
Open_inf=Leaf("OID",2,1)
Send_virus=Leaf("ASVVI",9,100 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",30,30 )

Injectionvia=Node(";",Interval(2,9),"IVRD")
Infectingac=Node("||",Interval(10,17),"IC")
selfi=Node("&",Interval(10,33),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)
Tree_SI= Attack_tree(selfi,Steal_cert,Tree_infecting)


#generate the pdf for attack tree
draw_attack_tree(Tree_infecting,'example')
Tree_2= propagate(Tree_infecting)
draw_attack_tree(Tree_infecting,'example_analysis')


