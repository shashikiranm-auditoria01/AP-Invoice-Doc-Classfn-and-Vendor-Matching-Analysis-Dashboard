select
-- COUNT(*)
swre.wk_result_id as 'DocID', swre.message_id as 'messageID', t.name as 'tenantName',
a.write_status as 'write_status', swre.created_at as 'created_at', swre.updated_at as 'updated_at',
swre.original_json->>'$.vendorName' as 'AAI vendorName', swre.final_json->>'$.vendorName' as 'Customer vendorName',
swre.original_json->>'$.aaiEntityId' as 'AAI entityID', swre.final_json->>'$.aaiEntityId' as 'Customer entityID',
se.entity_name as 'customer entity_name',
JSON_UNQUOTE(JSON_EXTRACT(a.record, '$.recordType')) AS 'Final Record Type',
    JSON_UNQUOTE(JSON_EXTRACT(a.session, '$.originalRecordType')) AS 'Original Record Type',
    JSON_UNQUOTE(JSON_EXTRACT(a.record, '$.invoiceNumber')) AS 'Invoice #',
    JSON_UNQUOTE(JSON_EXTRACT(a.record, '$.vendorName')) AS vendorname,
    JSON_UNQUOTE(JSON_EXTRACT(a.session, '$.attachments[0].filename')) AS attachmentFileName,
    JSON_UNQUOTE(JSON_EXTRACT(a.session, '$.attachments[0].key')) AS extractedFileS3Location,
    JSON_UNQUOTE(JSON_EXTRACT(a.session, '$.originalAttachment.filename')) AS originalAttachmentFileName,
    JSON_UNQUOTE(JSON_EXTRACT(a.session, '$.originalAttachment.attchment[0].key')) AS S3Location
from sor.wk_result_edits swre
LEFT JOIN sor.wk_inst_result a on swre.wk_result_id = a.id
LEFT JOIN tenant.tenant t on t.id=swre.tenant_id
LEFT JOIN sor.entity se on se.entity_id=swre.final_json->>'$.aaiEntityId'
 where swre.tenant_id='665247456933969920' and a.write_status=1
  and  swre.created_at >= '2026-03-01 00:00:01' AND swre.created_at <= '2026-03-31 11:00:44'
 and  swre.updated_at >= '2026-03-01 00:00:01' AND swre.updated_at <= '2026-03-31 11:00:44'
--  AND swre.original_json->>'$.aaiEntityId'!=swre.final_json->>'$.aaiEntityId'
-- AND swre.original_json ->> '$.vendorName' != swre.final_json ->> '$.vendorName'
 AND swre.original_json->>'$.recordType'!=swre.final_json->>'$.recordType'
 ORDER BY swre.updated_at DESC

For the above query is for checking three scenarios 1. entityName mismatches 2. document classification Issues 3. vendorName matching Issues so, for the above task we would review these so you need to create a seperate section for this i mean query pulling not review UI Part, as UI remains same but you need to add entityName related in the UI i guess  also when user validated these three sceanrios for recordType, entityName and vendorName display other cards as usual just that entityName is not ther in UI we need to add and this logic to pull mismatches for recordType and vendorName is also not there yet this will be also need to be added.
this line is for checking for a given tenant and date range where there are entityName mismatches original_json is where AAI or NLU given value and final_json is customer edited value AND swre.original_json->>'$.aaiEntityId'!=swre.final_json->>'$.aaiEntityId'
this line is for checking for a given tenant and date range where there are recordType mismatches original_json is where AAI or NLU given recordType and final_json is customer modified recordType  AND swre.original_json->>'$.recordType'!=swre.final_json->>'$.recordType'
this line is for checking for a given tenant and date range where there are vendorName mismatches original_json is where AAI or NLU given vendorName and final_json is customer modified vendorName  AND swre.original_json->>'$.vendorName'!=swre.final_json->>'$.vendorName'