from optimizer_as_list import *

interval_root = Interval(1, 10)
interval_left_sub = Interval(2, 8)
interval_right_sub = Interval(2, 7)
Insert_rem=Leaf("IRID",2,10)
Open_inf=Leaf("OID",2,14)
Send_virus=Leaf("ASVVI",2,25 )
Loading_main=Leaf("LMD",1,0 )
Steal_cert=Leaf("SDC",160,1 )

Injectionvia=Node("&",Interval(5,16),"IVRD")
Infectingac=Node("||",Interval(3,12),"IC")
selfi=Node("&",Interval(10,200),"SI")

Tree_injection= Attack_tree(Injectionvia,Open_inf , Insert_rem)
Tree_infecting= Attack_tree(Infectingac, Send_virus, Tree_injection)



                 
draw_attack_tree(Tree_infecting, 'paperex_before_prop')
draw_attack_tree(propagate(Tree_infecting), 'paperex_after_prop')
synthetize(Tree_infecting)
optimize(Tree_infecting)