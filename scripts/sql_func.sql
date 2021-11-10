create function _nextval(name varchar(50))    
returns integer      
begin     
declare _cur int;   
declare _maxvalue int;  -- 接收最大值   
declare _increment int; -- 接收增长步数   
-- select _maxvalue into higher, _cur into current from unique_id_tbl where seq_name = name; 
set _increment = 1;
set _cur = (select current from unique_id_tbl where seq_name = name);
set _maxvalue = (select higher from unique_id_tbl where seq_name = name);
update unique_id_tbl                      -- 更新当前值   
 set current = _cur + _increment     
 where seq_name = name ;     
if(_cur + _increment >= _maxvalue) then  -- 判断是都达到最大值   
      update unique_id_tbl     
        set current = minval     
        where seq_name = name ;   
end if;
return _cur;     
end;