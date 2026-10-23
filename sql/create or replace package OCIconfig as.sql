create or replace package OCIconfig as 

     --
    -- grant execute on dbms_cloud to iot;
    -- set ACL to allow *oraclecloud.com if run in OCI1
    --
    OCItenancyOCID varchar2(100) :=NULL;
    OCIuserOCID varchar2(100) :=NULL;
    OCIfingerPrint varchar2(100) :=NULL;
    OCIprivateKey varchar2(2000) := NULL;

    lastError varchar2(1000);
    procedure setOCIProperties(p_tenancyOCID in varchar2, p_userOCID in varchar2, p_fingerPrint in varchar2,p_privateKey in varchar2, region in varchar2, p_topicOCID in VARCHAR2);
    function createCredential(p_name in varchar2) return boolean;
end OCIconfig;
/
create or replace package body OCIconfig as 

     --
    -- grant execute on dbms_cloud to iot;
    -- set ACL to allow *oraclecloud.com if run in OCI1
    --
    procedure setOCIProperties(p_tenancyOCID in varchar2, p_userOCID in varchar2, p_fingerPrint in varchar2,p_privateKey in varchar2, region in varchar2,p_topicOCID in varchar2) is
    begin
        OCItenancyOCID  := p_tenancyOCID;
        OCIuserOCID  := p_userOCID;
        OCIfingerPrint  := p_fingerPrint;
        OCIprivateKey  := p_privateKey;
    end;

    function createCredential(p_name in varchar2) return boolean is
    BEGIN
        DBMS_CLOUD.CREATE_CREDENTIAL(
        credential_name => p_name,
        user_ocid       => OCIuserOCID,
        tenancy_ocid    => OCItenancyOCID,
        private_key     => OCIprivatekey,
        fingerprint     => OCIfingerPrint,
        comments        => 'test cred'
        );
        exception when OTHERS THEN
            raise_application_error(-20100,'credentials failed');
            return FALSE;
        return true;
    END;
end OCIconfig;
/

create procedure createExternalTable AS
BEGIN
    null;
end;
/
create or replace procedure setOCIParameters AS
BEGIN
    null;
end;
/
