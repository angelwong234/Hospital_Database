-- Nikhita Puthuveetil and Angel Wong
create view outpatient_procedure_info (hospital_id, hospital_name, doctor_name, outpatient_procedure_name, outpatient_cost) as
select p.hospital_id,
(select hospital_name from hospitals where p.hospital_id = hospitals.hospital_id) hospital_name, 
(select doctor_name from doctors where p.doctor_id = doctors.doctor_id) doctor_name, 
p.outpatient_procedure_name, o.cost_of_procedure 
from performs_outpatients p join outpatients o
on p.outpatient_procedure_name = o.outpatient_procedure_name and 
p.hospital_id = o.hospital_id;

create view inpatient_procedure_info (hospital_id, hospital_name, doctor_name, inpatient_procedure_name, inpatient_cost, cost_of_stay) as
select p.hospital_id,
(select hospital_name from hospitals where p.hospital_id = hospitals.hospital_id) hospital_name, 
(select doctor_name from doctors where p.doctor_id = doctors.doctor_id) doctor_name, 
p.inpatient_procedure_name, 
i.cost_of_procedure,
i.cost_of_stay_per_night
from performs_inpatients p join inpatients i
on p.inpatient_procedure_name = i.inpatient_procedure_name and 
p.hospital_id = i.hospital_id;

create view department_info (hospital_id, hospital_name, department_name, ranking, wait_time) as
select hospital_id, (select hospital_name from hospitals p where p.hospital_id = hospital_departments.hospital_id),
department_name, ranking, wait_time
from hospital_departments;


create or replace trigger log_admins
before insert or delete or update on users for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'users',
      'Username ' || :NEW.Username || ' added');
    end if;
    if updating
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'users',
                'Username ' || :OLD.Username || ' changed email');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'users',
                'Username ' || :OLD.Username || ' removed');
    end if;
end;
/

create or replace trigger log_hospitals
before insert or delete on hospitals for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'hospitals',
      'Hospital ' || :NEW.Hospital_Name || ' added');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'hospitals',
                'Hospital ' || :OLD.Hospital_Name || ' removed');
    end if;
end;
/

create or replace trigger log_doctors
before insert or delete on doctors for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'doctors',
      'Dr. ' || :NEW.Doctor_Name || ' added');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'doctors',
                'Dr. ' || :OLD.Doctor_Name || ' removed');
    end if;
end;
/

create or replace trigger log_credentials
before insert on credentials for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'credentials',
      'New credential (' || :NEW.place_of_education || ') added for Doctor ID ' || :NEW.Doctor_ID);
    end if;
end;
/

create or replace trigger log_specialization
before insert on specializations for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'specializations',
      'New specialization (' || :NEW.specialization || ') added for Doctor ID ' || :NEW.Doctor_ID);
    end if;
end;
/

create or replace trigger log_phone
before insert or delete or update on phone_numbers for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'phone_numbers',
      'Phone number added for Doctor ID ' || '' || :NEW.Doctor_ID);
    end if;
    if updating
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'phone_numbers',
                'Phone number updated for Doctor ID ' || '' || :NEW.Doctor_ID);
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'phone_numbers',
                'Phone number deleted for Doctor ID ' || '' || :OLD.Doctor_ID);
    end if;
end;
/

create or replace trigger log_departments
before insert or delete or update on hospital_departments for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'hospital departments',
      'Department of ' || :NEW.Department_name || ' added');
    end if;
    if updating
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'hospital departments',
                'Department of ' || :NEW.Department_name || ' updated');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'hospital departments',
                'Department of ' || :OLD.Department_name || ' deleted');
    end if;
end;
/


create or replace trigger log_inpatients
before insert or delete or update on inpatients for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'inpatients',
      :NEW.Inpatient_procedure_name || '' || ' added');
    end if;
    if updating
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'inpatients',
                :NEW.Inpatient_procedure_name || '' || ' updated');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'inpatients',
                :OLD.Inpatient_procedure_name || '' || ' removed');
    end if;
end;
/

create or replace trigger log_outpatients
before insert or delete or update on outpatients for each row
begin
    if inserting
      then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'outpatients',
      :NEW.outpatient_procedure_name || '' || ' added');
    end if;
    if updating
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'outpatients',
                :NEW.outpatient_procedure_name || '' || ' updated');
    end if;
    if deleting
        then insert into hospital_db_logs values(hospital_db_log_seq.nextval, SYSDATE, 'outpatients',
                :OLD.outpatient_procedure_name || '' || ' removed');
    end if;
end;
/

