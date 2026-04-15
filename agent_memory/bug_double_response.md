BUG: Zadvoenie otvetov Jarvisa
Data: 11.04.2026
Simptom: Na odno soobshchenie prikhodyat dva identichnyh otveta
Prichina: Veroyatno dva agenta v agent_router matchatsya na odin trigger
Reshenie: Proverit agent_router.py - ubrat dublirovanie pravil ili dobavit flag "already_handled"
Prioritet: sredniy, ispravit do sleduyushchego sprinta
