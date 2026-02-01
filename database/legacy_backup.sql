--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.1
-- Dumped by pg_dump version 9.6.1

-- Started on 2017-04-24 14:58:44 EDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE isodb;
--
-- TOC entry 3284 (class 1262 OID 16390)
-- Name: isodb; Type: DATABASE; Schema: -; Owner: isodbadmin
--

CREATE DATABASE isodb WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


ALTER DATABASE isodb OWNER TO isodbadmin;

\connect isodb

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 1 (class 3079 OID 13308)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 3287 (class 0 OID 0)
-- Dependencies: 1
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 220 (class 1259 OID 27362)
-- Name: al_account_keys; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE al_account_keys (
    al_account_id bigint NOT NULL,
    al_customer_name text,
    api_key text NOT NULL,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE al_account_keys OWNER TO isodbadmin;

--
-- TOC entry 219 (class 1259 OID 27349)
-- Name: al_accounts; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE al_accounts (
    al_account_id bigint NOT NULL,
    aws_account_id bigint,
    al_account_name text NOT NULL,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    last_updated timestamp with time zone,
    api_key text
);


ALTER TABLE al_accounts OWNER TO isodbadmin;

--
-- TOC entry 3289 (class 0 OID 0)
-- Dependencies: 219
-- Name: TABLE al_accounts; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE al_accounts IS 'table for mapping aws accounts and alert logic accounts, starting with Threat Manager and Log manager accounts; add Cloud Insight later';


--
-- TOC entry 217 (class 1259 OID 27333)
-- Name: al_overview; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE al_overview (
    al_account_id bigint NOT NULL,
    account_name text NOT NULL,
    tm_appliance_count bigint,
    tm_policies_count bigint,
    tm_protected_hosts_count bigint,
    tm_hosts_count bigint,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE al_overview OWNER TO isodbadmin;

--
-- TOC entry 3291 (class 0 OID 0)
-- Dependencies: 217
-- Name: TABLE al_overview; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE al_overview IS 'Summary Metrics from Alert Logic';


--
-- TOC entry 190 (class 1259 OID 16447)
-- Name: al_remediations; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE al_remediations (
    ts_inserted timestamp without time zone DEFAULT now() NOT NULL,
    al_remediations_json jsonb,
    al_remediation_id bigint NOT NULL
);


ALTER TABLE al_remediations OWNER TO isodbadmin;

--
-- TOC entry 189 (class 1259 OID 16445)
-- Name: al_remediations_al_remediation_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE al_remediations_al_remediation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE al_remediations_al_remediation_id_seq OWNER TO isodbadmin;

--
-- TOC entry 3294 (class 0 OID 0)
-- Dependencies: 189
-- Name: al_remediations_al_remediation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: isodbadmin
--

ALTER SEQUENCE al_remediations_al_remediation_id_seq OWNED BY al_remediations.al_remediation_id;


--
-- TOC entry 210 (class 1259 OID 16998)
-- Name: aud_aws_instances; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_aws_instances (
    aws_account_id bigint NOT NULL,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    instance_json jsonb NOT NULL,
    instanceid character(50) NOT NULL
);


ALTER TABLE aud_aws_instances OWNER TO isodbadmin;

--
-- TOC entry 3296 (class 0 OID 0)
-- Dependencies: 210
-- Name: TABLE aud_aws_instances; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE aud_aws_instances IS 'table to store results from ec2 describe_instances; ';


--
-- TOC entry 193 (class 1259 OID 16482)
-- Name: aud_iam_group_details_aud_iam_group_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_iam_group_details_aud_iam_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_iam_group_details_aud_iam_group_id_seq OWNER TO isodbadmin;

--
-- TOC entry 194 (class 1259 OID 16484)
-- Name: aud_iam_groups; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_iam_groups (
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    group_json jsonb,
    insert_id bigint DEFAULT nextval('aud_iam_group_details_aud_iam_group_id_seq'::regclass) NOT NULL,
    arn text,
    groupid text,
    path text,
    createdate timestamp with time zone,
    groupname text,
    aws_account_id bigint NOT NULL
);


ALTER TABLE aud_iam_groups OWNER TO isodbadmin;

--
-- TOC entry 198 (class 1259 OID 16520)
-- Name: aud_iam_policies_aud_iam_policies_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_iam_policies_aud_iam_policies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_iam_policies_aud_iam_policies_id_seq OWNER TO isodbadmin;

--
-- TOC entry 199 (class 1259 OID 16522)
-- Name: aud_iam_policies; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_iam_policies (
    policy_json jsonb,
    insert_id bigint DEFAULT nextval('aud_iam_policies_aud_iam_policies_id_seq'::regclass) NOT NULL,
    arn text,
    path text,
    createdate timestamp with time zone,
    policyname text,
    aws_account_id bigint NOT NULL,
    attachmentcount integer,
    isattachable boolean NOT NULL,
    defaultversionid text,
    updatedate timestamp without time zone,
    last_audited timestamp with time zone DEFAULT now() NOT NULL,
    policyid text NOT NULL,
    policy_document jsonb,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    policygroups jsonb,
    policyusers jsonb,
    policyroles jsonb
);


ALTER TABLE aud_iam_policies OWNER TO isodbadmin;

--
-- TOC entry 197 (class 1259 OID 16504)
-- Name: aud_iam_policy_details_aud_iam_policy_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_iam_policy_details_aud_iam_policy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_iam_policy_details_aud_iam_policy_id_seq OWNER TO isodbadmin;

--
-- TOC entry 192 (class 1259 OID 16470)
-- Name: aud_iam_roles; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_iam_roles (
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    role_json jsonb,
    insert_id bigint NOT NULL,
    arn text,
    roleid text,
    path text,
    createdate timestamp with time zone,
    rolename text,
    aws_account_id bigint NOT NULL,
    assumerolepolicydocument jsonb
);


ALTER TABLE aud_iam_roles OWNER TO isodbadmin;

--
-- TOC entry 191 (class 1259 OID 16468)
-- Name: aud_iam_role_details_aud_iam_role_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_iam_role_details_aud_iam_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_iam_role_details_aud_iam_role_id_seq OWNER TO isodbadmin;

--
-- TOC entry 3304 (class 0 OID 0)
-- Dependencies: 191
-- Name: aud_iam_role_details_aud_iam_role_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: isodbadmin
--

ALTER SEQUENCE aud_iam_role_details_aud_iam_role_id_seq OWNED BY aud_iam_roles.insert_id;


--
-- TOC entry 195 (class 1259 OID 16493)
-- Name: aud_iam_user_details_aud_iam_user_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_iam_user_details_aud_iam_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_iam_user_details_aud_iam_user_id_seq OWNER TO isodbadmin;

--
-- TOC entry 196 (class 1259 OID 16495)
-- Name: aud_iam_users; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_iam_users (
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    user_json jsonb,
    insert_id bigint DEFAULT nextval('aud_iam_user_details_aud_iam_user_id_seq'::regclass) NOT NULL,
    arn text,
    userid text,
    path text,
    createdate timestamp with time zone,
    username text,
    aws_account_id bigint NOT NULL,
    passwordlastused timestamp with time zone
);


ALTER TABLE aud_iam_users OWNER TO isodbadmin;

--
-- TOC entry 209 (class 1259 OID 16988)
-- Name: aud_tags; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aud_tags (
    aws_account_id bigint NOT NULL,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    resourcetype character(50) NOT NULL,
    resourceid character(50) NOT NULL,
    tagkey character(128) NOT NULL,
    tag_insert_id bigint NOT NULL,
    tagvalue character(256) NOT NULL
);


ALTER TABLE aud_tags OWNER TO isodbadmin;

--
-- TOC entry 3308 (class 0 OID 0)
-- Dependencies: 209
-- Name: TABLE aud_tags; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE aud_tags IS 'table to store output from boto3 ec2 describe_tags';


--
-- TOC entry 208 (class 1259 OID 16986)
-- Name: aud_tags_tag_insert_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE aud_tags_tag_insert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE aud_tags_tag_insert_id_seq OWNER TO isodbadmin;

--
-- TOC entry 3310 (class 0 OID 0)
-- Dependencies: 208
-- Name: aud_tags_tag_insert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: isodbadmin
--

ALTER SEQUENCE aud_tags_tag_insert_id_seq OWNED BY aud_tags.tag_insert_id;


--
-- TOC entry 226 (class 1259 OID 34819)
-- Name: audit_users_and_policies; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE audit_users_and_policies (
    aws_account_name character varying,
    aws_account_id bigint,
    arn text,
    userid text,
    username text,
    insert_ts date,
    policyname text,
    policy_document jsonb,
    policyarn text
);


ALTER TABLE audit_users_and_policies OWNER TO isodbadmin;

--
-- TOC entry 202 (class 1259 OID 16629)
-- Name: auditor_users; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE auditor_users (
    username character varying,
    email_address character varying NOT NULL
);


ALTER TABLE auditor_users OWNER TO isodbadmin;

--
-- TOC entry 3312 (class 0 OID 0)
-- Dependencies: 202
-- Name: TABLE auditor_users; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE auditor_users IS 'users with access to ISO Auditor tool; also used as a data source for mapping aws account IDs to account owners ';


--
-- TOC entry 204 (class 1259 OID 16655)
-- Name: aws_account_roles; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aws_account_roles (
    account_role character varying NOT NULL,
    aws_account_id bigint NOT NULL,
    email_address character varying NOT NULL
);


ALTER TABLE aws_account_roles OWNER TO isodbadmin;

--
-- TOC entry 3314 (class 0 OID 0)
-- Dependencies: 204
-- Name: TABLE aws_account_roles; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE aws_account_roles IS 'create a mapping of roles (Invoice Approve, Operational contact, Security Contact) to users and accounts.';


--
-- TOC entry 201 (class 1259 OID 16620)
-- Name: aws_accounts; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aws_accounts (
    aws_account_id bigint NOT NULL,
    aws_account_name character varying NOT NULL,
    root_email character varying,
    account_active boolean DEFAULT false NOT NULL,
    iam_signin_link character varying,
    mss_cops_root_access boolean
);


ALTER TABLE aws_accounts OWNER TO isodbadmin;

--
-- TOC entry 218 (class 1259 OID 27341)
-- Name: aws_accounts_al_accounts; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aws_accounts_al_accounts (
    aws_account_id bigint,
    al_account_id bigint
);


ALTER TABLE aws_accounts_al_accounts OWNER TO isodbadmin;

--
-- TOC entry 203 (class 1259 OID 16637)
-- Name: aws_accounts_to_auditor_users; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aws_accounts_to_auditor_users (
    aws_account_id bigint NOT NULL,
    email_address character varying NOT NULL
);


ALTER TABLE aws_accounts_to_auditor_users OWNER TO isodbadmin;

--
-- TOC entry 200 (class 1259 OID 16585)
-- Name: aws_cross_account_roles; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE aws_cross_account_roles (
    aws_account_id bigint NOT NULL,
    role_arn text NOT NULL,
    working boolean,
    insert_ts timestamp with time zone NOT NULL,
    last_used_ts timestamp with time zone
);


ALTER TABLE aws_cross_account_roles OWNER TO isodbadmin;

--
-- TOC entry 3319 (class 0 OID 0)
-- Dependencies: 200
-- Name: TABLE aws_cross_account_roles; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE aws_cross_account_roles IS 'A table to collect ISO''s cross account roles in the various Turner AWS accounts.  At a mininum it needs Account Number + Role ARN.  It may also need a Record Insert TimeStamp for compliance tracking, and maybe a column for "Is it Working?" and "Last Used Timestamp".  That way we can track broken roles.';


--
-- TOC entry 187 (class 1259 OID 16396)
-- Name: cht_aws_instances; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE cht_aws_instances (
    aws_account_name text,
    aws_amazon_name text,
    aws_account_number bigint NOT NULL,
    aws_instance_name text,
    aws_instance_id text NOT NULL,
    public_ip inet,
    aws_product text,
    aws_api_name text,
    aws_zone_name text,
    attached_ebs bigint,
    launched_by text,
    public_dns text,
    private_ip inet NOT NULL,
    private_dns text,
    vpc_id text,
    subnet text,
    first_discovered timestamp without time zone,
    ts_inserted timestamp without time zone NOT NULL,
    cht_aws_instance_id bigint NOT NULL
);


ALTER TABLE cht_aws_instances OWNER TO isodbadmin;

--
-- TOC entry 3321 (class 0 OID 0)
-- Dependencies: 187
-- Name: TABLE cht_aws_instances; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE cht_aws_instances IS 'Account Name,Amazon Name,Owner Id,
Instance Name,Instance Id,Public IP,
Product,API Name,Zone Name,
Attached EBS,Launched By,Public DNS,Private IP,Private DNS,VPC Id,Subnet,
First Discovered';


--
-- TOC entry 188 (class 1259 OID 16404)
-- Name: cht_aws_instances_cht_aws_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE cht_aws_instances_cht_aws_instance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cht_aws_instances_cht_aws_instance_id_seq OWNER TO isodbadmin;

--
-- TOC entry 3323 (class 0 OID 0)
-- Dependencies: 188
-- Name: cht_aws_instances_cht_aws_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: isodbadmin
--

ALTER SEQUENCE cht_aws_instances_cht_aws_instance_id_seq OWNED BY cht_aws_instances.cht_aws_instance_id;


--
-- TOC entry 215 (class 1259 OID 27309)
-- Name: cht_aws_users; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE cht_aws_users (
    aws_account_id bigint NOT NULL,
    insert_id bigint NOT NULL,
    cht_user_json jsonb,
    insert_ts timestamp without time zone DEFAULT now() NOT NULL,
    arn text NOT NULL,
    path text,
    user_id text NOT NULL,
    created_date timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    mfa_status boolean,
    username text
);


ALTER TABLE cht_aws_users OWNER TO isodbadmin;

--
-- TOC entry 214 (class 1259 OID 27307)
-- Name: cht_aws_users_insert_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE cht_aws_users_insert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cht_aws_users_insert_id_seq OWNER TO isodbadmin;

--
-- TOC entry 3326 (class 0 OID 0)
-- Dependencies: 214
-- Name: cht_aws_users_insert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: isodbadmin
--

ALTER SEQUENCE cht_aws_users_insert_id_seq OWNED BY cht_aws_users.insert_id;


--
-- TOC entry 212 (class 1259 OID 17055)
-- Name: cht_instances_insert_id_seq; Type: SEQUENCE; Schema: public; Owner: isodbadmin
--

CREATE SEQUENCE cht_instances_insert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE cht_instances_insert_id_seq OWNER TO isodbadmin;

--
-- TOC entry 213 (class 1259 OID 17057)
-- Name: cht_instances; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE cht_instances (
    cht_instance_insert_id bigint DEFAULT nextval('cht_instances_insert_id_seq'::regclass) NOT NULL,
    instance_id character(50),
    dns text,
    groups text,
    instance_ip cidr,
    sshkey character(125),
    launch_date timestamp with time zone,
    launched_by text,
    instance_name text,
    owner_email text,
    private_dns text,
    private_ip cidr,
    instance_tags text,
    updated_at timestamp with time zone,
    vpc_id character(50),
    cht_instance_json jsonb,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL,
    aws_account_id bigint NOT NULL
);


ALTER TABLE cht_instances OWNER TO isodbadmin;

--
-- TOC entry 206 (class 1259 OID 16972)
-- Name: cht_subnets; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE cht_subnets (
    aws_account_id bigint NOT NULL,
    aws_account_name character varying,
    subnet_id character varying NOT NULL,
    subnet_name character varying NOT NULL,
    vpc_id character varying NOT NULL,
    subnet_state character varying,
    cidr cidr NOT NULL,
    available_ips bigint
);


ALTER TABLE cht_subnets OWNER TO isodbadmin;

--
-- TOC entry 3328 (class 0 OID 0)
-- Dependencies: 206
-- Name: TABLE cht_subnets; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE cht_subnets IS 'https://apps.cloudhealthtech.com/assets/aws/vpc/subnets';


--
-- TOC entry 207 (class 1259 OID 16978)
-- Name: cht_vpcs; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE cht_vpcs (
    aws_account_id bigint NOT NULL,
    vpc_name character varying NOT NULL,
    vpc_id character varying NOT NULL,
    vpc_state character varying,
    vpc_cidr cidr NOT NULL,
    insert_ts timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE cht_vpcs OWNER TO isodbadmin;

--
-- TOC entry 3330 (class 0 OID 0)
-- Dependencies: 207
-- Name: TABLE cht_vpcs; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE cht_vpcs IS 'https://apps.cloudhealthtech.com/assets/aws/vpc/vpcs';


--
-- TOC entry 205 (class 1259 OID 16966)
-- Name: neteng_ip_allocation; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE neteng_ip_allocation (
    cidr cidr NOT NULL,
    cidr_name character varying NOT NULL,
    aws_account_id bigint
);


ALTER TABLE neteng_ip_allocation OWNER TO isodbadmin;

--
-- TOC entry 3332 (class 0 OID 0)
-- Dependencies: 205
-- Name: TABLE neteng_ip_allocation; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON TABLE neteng_ip_allocation IS 'http://docs.turner.com/display/NETENG/IP+Allocation#IPAllocation-10.61.0.0/16-AmazonVPCs';


--
-- TOC entry 216 (class 1259 OID 27329)
-- Name: view_account_overview; Type: TABLE; Schema: public; Owner: isodbadmin
--

CREATE TABLE view_account_overview (
    aws_account_name character varying,
    aws_account_id bigint,
    account_active boolean,
    "AWS Instance Count (CHT)" bigint
);

ALTER TABLE ONLY view_account_overview REPLICA IDENTITY NOTHING;


ALTER TABLE view_account_overview OWNER TO isodbadmin;

--
-- TOC entry 224 (class 1259 OID 31054)
-- Name: view_al_install_summary; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_al_install_summary AS
 SELECT ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
           FROM al_overview
          ORDER BY ((al_overview.insert_ts)::date) DESC
         LIMIT 1) AS date_collected,
    ( SELECT count(*) AS count
           FROM cht_instances
          WHERE ((cht_instances.insert_ts)::date IN ( SELECT DISTINCT (cht_instances_1.insert_ts)::date AS insert_ts
                   FROM cht_instances cht_instances_1
                  ORDER BY ((cht_instances_1.insert_ts)::date) DESC
                 LIMIT 1))) AS "AWS Instances",
    ( SELECT (sum(a.tm_protected_hosts_count))::integer AS sum
           FROM al_overview a
          WHERE ((a.insert_ts)::date IN ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
                   FROM al_overview
                  ORDER BY ((al_overview.insert_ts)::date) DESC
                 LIMIT 1))) AS "TM Protected Host Count",
    ((( SELECT (sum(a.tm_protected_hosts_count))::double precision AS sum
           FROM al_overview a
          WHERE ((a.insert_ts)::date IN ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
                   FROM al_overview
                  ORDER BY ((al_overview.insert_ts)::date) DESC
                 LIMIT 1))) / (( SELECT count(*) AS count
           FROM cht_instances
          WHERE ((cht_instances.insert_ts)::date IN ( SELECT DISTINCT (cht_instances_1.insert_ts)::date AS insert_ts
                   FROM cht_instances cht_instances_1
                  ORDER BY ((cht_instances_1.insert_ts)::date) DESC
                 LIMIT 1))))::double precision) * (100)::double precision) AS "Percent Agent Installed",
    ( SELECT (sum(a.tm_hosts_count))::integer AS sum
           FROM al_overview a
          WHERE ((a.insert_ts)::date IN ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
                   FROM al_overview
                  ORDER BY ((al_overview.insert_ts)::date) DESC
                 LIMIT 1))) AS "TM Hosts Count",
    ( SELECT (sum(a.tm_appliance_count))::integer AS sum
           FROM al_overview a
          WHERE ((a.insert_ts)::date IN ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
                   FROM al_overview
                  ORDER BY ((al_overview.insert_ts)::date) DESC
                 LIMIT 1))) AS "TM Appliance Count",
    (( SELECT count(*) AS count
           FROM cht_vpcs
          WHERE ((cht_vpcs.insert_ts)::date IN ( SELECT DISTINCT (cht_vpcs_1.insert_ts)::date AS insert_ts
                   FROM cht_vpcs cht_vpcs_1
                  ORDER BY ((cht_vpcs_1.insert_ts)::date) DESC
                 LIMIT 1))))::double precision AS "AWS VPCs",
    (((( SELECT (sum(a.tm_appliance_count))::integer AS sum
           FROM al_overview a
          WHERE ((a.insert_ts)::date IN ( SELECT DISTINCT (al_overview.insert_ts)::date AS insert_ts
                   FROM al_overview
                  ORDER BY ((al_overview.insert_ts)::date) DESC
                 LIMIT 1))))::double precision / (( SELECT count(*) AS count
           FROM cht_vpcs
          WHERE ((cht_vpcs.insert_ts)::date IN ( SELECT DISTINCT (cht_vpcs_1.insert_ts)::date AS insert_ts
                   FROM cht_vpcs cht_vpcs_1
                  ORDER BY ((cht_vpcs_1.insert_ts)::date) DESC
                 LIMIT 1))))::double precision) * (100)::double precision) AS "Percent Appliances Installed";


ALTER TABLE view_al_install_summary OWNER TO isodbadmin;

--
-- TOC entry 223 (class 1259 OID 29677)
-- Name: view_al_status; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_al_status AS
 SELECT al_accounts.aws_account_id,
    al_overview.al_account_id,
    al_overview.account_name,
    ( SELECT count(*) AS count
           FROM cht_instances
          WHERE ((cht_instances.aws_account_id = al_accounts.aws_account_id) AND ((cht_instances.insert_ts)::date IN ( SELECT DISTINCT (cht_instances_1.insert_ts)::date AS insert_ts
                   FROM cht_instances cht_instances_1
                  ORDER BY ((cht_instances_1.insert_ts)::date) DESC
                 LIMIT 1)))) AS instance_counts,
    al_overview.tm_protected_hosts_count,
    al_overview.tm_hosts_count,
    (( SELECT count(*) AS count
           FROM cht_vpcs
          WHERE ((cht_vpcs.aws_account_id = al_accounts.aws_account_id) AND ((cht_vpcs.insert_ts)::date IN ( SELECT DISTINCT (cht_vpcs_1.insert_ts)::date AS insert_ts
                   FROM cht_vpcs cht_vpcs_1
                  ORDER BY ((cht_vpcs_1.insert_ts)::date) DESC
                 LIMIT 1)))))::double precision AS aws_vpcs,
    al_overview.tm_appliance_count,
    (al_overview.insert_ts)::date AS insert_ts
   FROM (al_accounts
     LEFT JOIN al_overview ON ((al_accounts.al_account_id = al_overview.al_account_id)))
  WHERE ((al_overview.insert_ts)::date IN ( SELECT DISTINCT (al_overview_1.insert_ts)::date AS insert_ts
           FROM al_overview al_overview_1
          ORDER BY ((al_overview_1.insert_ts)::date) DESC
         LIMIT 1));


ALTER TABLE view_al_status OWNER TO isodbadmin;

--
-- TOC entry 228 (class 1259 OID 38811)
-- Name: view_audit_policy_map; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_audit_policy_map AS
 SELECT r.aws_account_id,
    r.arn,
    r.policyname,
    r.policy_document,
    (jsonb_array_elements(r.policyusers) ->> 'UserName'::text) AS thisname,
    (jsonb_array_elements(r.policyusers) ->> 'UserId'::text) AS thisid,
    (r.insert_ts)::date AS insert_ts
   FROM aud_iam_policies r
  WHERE (((r.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_policies.insert_ts)::date AS insert_ts
           FROM aud_iam_policies
          GROUP BY ((aud_iam_policies.insert_ts)::date)
          ORDER BY ((aud_iam_policies.insert_ts)::date) DESC
         LIMIT 1)) AND (jsonb_array_length(r.policyusers) > 0))
UNION
 SELECT r.aws_account_id,
    r.arn,
    r.policyname,
    r.policy_document,
    (jsonb_array_elements(r.policyroles) ->> 'RoleName'::text) AS thisname,
    (jsonb_array_elements(r.policyroles) ->> 'RoleId'::text) AS thisid,
    (r.insert_ts)::date AS insert_ts
   FROM aud_iam_policies r
  WHERE (((r.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_policies.insert_ts)::date AS insert_ts
           FROM aud_iam_policies
          GROUP BY ((aud_iam_policies.insert_ts)::date)
          ORDER BY ((aud_iam_policies.insert_ts)::date) DESC
         LIMIT 1)) AND (jsonb_array_length(r.policyroles) > 0))
UNION
 SELECT r.aws_account_id,
    r.arn,
    r.policyname,
    r.policy_document,
    (jsonb_array_elements(r.policygroups) ->> 'GroupName'::text) AS thisname,
    (jsonb_array_elements(r.policygroups) ->> 'GroupId'::text) AS thisid,
    (r.insert_ts)::date AS insert_ts
   FROM aud_iam_policies r
  WHERE (((r.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_policies.insert_ts)::date AS insert_ts
           FROM aud_iam_policies
          GROUP BY ((aud_iam_policies.insert_ts)::date)
          ORDER BY ((aud_iam_policies.insert_ts)::date) DESC
         LIMIT 1)) AND (jsonb_array_length(r.policygroups) > 0));


ALTER TABLE view_audit_policy_map OWNER TO isodbadmin;

--
-- TOC entry 227 (class 1259 OID 35242)
-- Name: view_audit_users; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_audit_users AS
 SELECT aws_accounts.aws_account_name,
    aud_iam_groups.aws_account_id,
    aud_iam_groups.arn,
    aud_iam_groups.groupid AS userid,
    aud_iam_groups.groupname AS username,
    (aud_iam_groups.insert_ts)::date AS insert_ts
   FROM aud_iam_groups,
    aws_accounts
  WHERE (((aud_iam_groups.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_groups_1.insert_ts)::date AS insert_ts
           FROM aud_iam_groups aud_iam_groups_1
          GROUP BY aud_iam_groups_1.insert_ts
          ORDER BY ((aud_iam_groups_1.insert_ts)::date) DESC
         LIMIT 1)) AND (aud_iam_groups.aws_account_id = aws_accounts.aws_account_id))
UNION
 SELECT aws_accounts.aws_account_name,
    aud_iam_roles.aws_account_id,
    aud_iam_roles.arn,
    aud_iam_roles.roleid AS userid,
    aud_iam_roles.rolename AS username,
    (aud_iam_roles.insert_ts)::date AS insert_ts
   FROM aud_iam_roles,
    aws_accounts
  WHERE (((aud_iam_roles.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_roles_1.insert_ts)::date AS insert_ts
           FROM aud_iam_roles aud_iam_roles_1
          GROUP BY aud_iam_roles_1.insert_ts
          ORDER BY ((aud_iam_roles_1.insert_ts)::date) DESC
         LIMIT 1)) AND (aud_iam_roles.aws_account_id = aws_accounts.aws_account_id))
UNION
 SELECT aws_accounts.aws_account_name,
    cht_aws_users.aws_account_id,
    cht_aws_users.arn,
    cht_aws_users.user_id AS userid,
    cht_aws_users.username,
    (cht_aws_users.insert_ts)::date AS insert_ts
   FROM cht_aws_users,
    aws_accounts
  WHERE (((cht_aws_users.insert_ts)::date IN ( SELECT DISTINCT (cht_aws_users_1.insert_ts)::date AS insert_ts
           FROM cht_aws_users cht_aws_users_1
          GROUP BY cht_aws_users_1.insert_ts
          ORDER BY ((cht_aws_users_1.insert_ts)::date) DESC
         LIMIT 1)) AND (cht_aws_users.aws_account_id = aws_accounts.aws_account_id))
UNION
 SELECT aws_accounts.aws_account_name,
    aud_iam_users.aws_account_id,
    aud_iam_users.arn,
    aud_iam_users.userid,
    aud_iam_users.username,
    (aud_iam_users.insert_ts)::date AS insert_ts
   FROM aud_iam_users,
    aws_accounts
  WHERE (((aud_iam_users.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_users_1.insert_ts)::date AS insert_ts
           FROM aud_iam_users aud_iam_users_1
          GROUP BY aud_iam_users_1.insert_ts
          ORDER BY ((aud_iam_users_1.insert_ts)::date) DESC
         LIMIT 1)) AND (aud_iam_users.aws_account_id = aws_accounts.aws_account_id));


ALTER TABLE view_audit_users OWNER TO isodbadmin;

--
-- TOC entry 221 (class 1259 OID 28530)
-- Name: view_aws_accounts_not_in_cht; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_aws_accounts_not_in_cht AS
 SELECT aws_accounts.aws_account_id AS a
   FROM aws_accounts
  WHERE (aws_accounts.account_active = true)
EXCEPT (
         SELECT cht_instances.aws_account_id AS a
           FROM cht_instances
        UNION
         SELECT cht_aws_users.aws_account_id AS a
           FROM cht_aws_users
        UNION
         SELECT cht_vpcs.aws_account_id AS a
           FROM cht_vpcs
);


ALTER TABLE view_aws_accounts_not_in_cht OWNER TO isodbadmin;

--
-- TOC entry 3339 (class 0 OID 0)
-- Dependencies: 221
-- Name: VIEW view_aws_accounts_not_in_cht; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON VIEW view_aws_accounts_not_in_cht IS 'AWS Account IDs in AWS_ACCOUNTS table that DO NOT EXIST in CHT tables ';


--
-- TOC entry 211 (class 1259 OID 17051)
-- Name: view_aws_instance_tags_last_24_hours; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_aws_instance_tags_last_24_hours AS
 SELECT t.aws_account_id,
    t.resourceid,
    t.tagkey,
    t.tagvalue
   FROM aud_tags t
  WHERE ((t.resourceid ~~ 'i-%'::text) AND (date_part('hour'::text, age(now(), t.insert_ts)) <= (24)::double precision))
  ORDER BY t.aws_account_id, t.resourceid;


ALTER TABLE view_aws_instance_tags_last_24_hours OWNER TO isodbadmin;

--
-- TOC entry 225 (class 1259 OID 33313)
-- Name: view_cloud_audit_review; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_cloud_audit_review AS
 SELECT DISTINCT (aud_iam_users.insert_ts)::date AS insert_date,
    ( SELECT count((aud_iam_users_1.insert_ts)::date) AS iam_user_count
           FROM aud_iam_users aud_iam_users_1
          WHERE ((aud_iam_users_1.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_users_2.insert_ts)::date AS insert_ts
                   FROM aud_iam_users aud_iam_users_2
                  ORDER BY ((aud_iam_users_2.insert_ts)::date) DESC
                 LIMIT 1))
          GROUP BY ((aud_iam_users_1.insert_ts)::date)
          ORDER BY ((aud_iam_users_1.insert_ts)::date) DESC) AS iam_user_count,
    ( SELECT count((aud_iam_groups.insert_ts)::date) AS iam_groups_count
           FROM aud_iam_groups
          WHERE ((aud_iam_groups.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_groups_1.insert_ts)::date AS insert_ts
                   FROM aud_iam_groups aud_iam_groups_1
                  ORDER BY ((aud_iam_groups_1.insert_ts)::date) DESC
                 LIMIT 1))
          GROUP BY ((aud_iam_groups.insert_ts)::date)
          ORDER BY ((aud_iam_groups.insert_ts)::date) DESC) AS iam_groups_count,
    ( SELECT count((aud_iam_roles.insert_ts)::date) AS iam_roles_count
           FROM aud_iam_roles
          WHERE ((aud_iam_roles.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_roles_1.insert_ts)::date AS insert_ts
                   FROM aud_iam_roles aud_iam_roles_1
                  ORDER BY ((aud_iam_roles_1.insert_ts)::date) DESC
                 LIMIT 1))
          GROUP BY ((aud_iam_roles.insert_ts)::date)
          ORDER BY ((aud_iam_roles.insert_ts)::date) DESC) AS iam_roles_count,
    ( SELECT count((aud_iam_policies.insert_ts)::date) AS iam_policies_count
           FROM aud_iam_policies
          WHERE ((aud_iam_policies.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_policies_1.insert_ts)::date AS insert_ts
                   FROM aud_iam_policies aud_iam_policies_1
                  ORDER BY ((aud_iam_policies_1.insert_ts)::date) DESC
                 LIMIT 1))
          GROUP BY ((aud_iam_policies.insert_ts)::date)
          ORDER BY ((aud_iam_policies.insert_ts)::date) DESC) AS iam_policies_count
   FROM aud_iam_users
  WHERE ((aud_iam_users.insert_ts)::date IN ( SELECT DISTINCT (aud_iam_users_1.insert_ts)::date AS insert_ts
           FROM aud_iam_users aud_iam_users_1
          ORDER BY ((aud_iam_users_1.insert_ts)::date) DESC
         LIMIT 1));


ALTER TABLE view_cloud_audit_review OWNER TO isodbadmin;

--
-- TOC entry 3342 (class 0 OID 0)
-- Dependencies: 225
-- Name: VIEW view_cloud_audit_review; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON VIEW view_cloud_audit_review IS 'produce a quick review of the rows inserted so the auditor script can return meaningful data to LAMBDA';


--
-- TOC entry 222 (class 1259 OID 28534)
-- Name: view_iam_policy_statement; Type: VIEW; Schema: public; Owner: isodbadmin
--

CREATE VIEW view_iam_policy_statement AS
 SELECT ((tp.policy_document -> 'Statement'::text) -> 'Action'::text)
   FROM aud_iam_policies tp
  WHERE (jsonb_typeof((tp.policy_document -> 'Statement'::text)) = 'object'::text)
UNION
 SELECT (te.value -> 'Action'::text)
   FROM aud_iam_policies tp,
    LATERAL jsonb_array_elements((tp.policy_document -> 'Statement'::text)) te(value)
  WHERE (jsonb_typeof((tp.policy_document -> 'Statement'::text)) <> 'object'::text);


ALTER TABLE view_iam_policy_statement OWNER TO isodbadmin;

--
-- TOC entry 3344 (class 0 OID 0)
-- Dependencies: 222
-- Name: VIEW view_iam_policy_statement; Type: COMMENT; Schema: public; Owner: isodbadmin
--

COMMENT ON VIEW view_iam_policy_statement IS 'starting point for evaluating the riskiness of policies';


--
-- TOC entry 3087 (class 2604 OID 16450)
-- Name: al_remediations al_remediation_id; Type: DEFAULT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY al_remediations ALTER COLUMN al_remediation_id SET DEFAULT nextval('al_remediations_al_remediation_id_seq'::regclass);


--
-- TOC entry 3089 (class 2604 OID 16473)
-- Name: aud_iam_roles insert_id; Type: DEFAULT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_iam_roles ALTER COLUMN insert_id SET DEFAULT nextval('aud_iam_role_details_aud_iam_role_id_seq'::regclass);


--
-- TOC entry 3101 (class 2604 OID 16992)
-- Name: aud_tags tag_insert_id; Type: DEFAULT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_tags ALTER COLUMN tag_insert_id SET DEFAULT nextval('aud_tags_tag_insert_id_seq'::regclass);


--
-- TOC entry 3086 (class 2604 OID 16406)
-- Name: cht_aws_instances cht_aws_instance_id; Type: DEFAULT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY cht_aws_instances ALTER COLUMN cht_aws_instance_id SET DEFAULT nextval('cht_aws_instances_cht_aws_instance_id_seq'::regclass);


--
-- TOC entry 3105 (class 2604 OID 27312)
-- Name: cht_aws_users insert_id; Type: DEFAULT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY cht_aws_users ALTER COLUMN insert_id SET DEFAULT nextval('cht_aws_users_insert_id_seq'::regclass);


--
-- TOC entry 3113 (class 2606 OID 16455)
-- Name: al_remediations al_remediations_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY al_remediations
    ADD CONSTRAINT al_remediations_pkey PRIMARY KEY (al_remediation_id);


--
-- TOC entry 3118 (class 2606 OID 16561)
-- Name: aud_iam_groups aud_iam_group_details_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_iam_groups
    ADD CONSTRAINT aud_iam_group_details_pkey PRIMARY KEY (insert_id);


--
-- TOC entry 3124 (class 2606 OID 16530)
-- Name: aud_iam_policies aud_iam_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_iam_policies
    ADD CONSTRAINT aud_iam_policies_pkey PRIMARY KEY (insert_id);


--
-- TOC entry 3115 (class 2606 OID 16478)
-- Name: aud_iam_roles aud_iam_role_details_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_iam_roles
    ADD CONSTRAINT aud_iam_role_details_pkey PRIMARY KEY (insert_id);


--
-- TOC entry 3121 (class 2606 OID 16503)
-- Name: aud_iam_users aud_iam_user_details_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_iam_users
    ADD CONSTRAINT aud_iam_user_details_pkey PRIMARY KEY (insert_id);


--
-- TOC entry 3130 (class 2606 OID 16636)
-- Name: auditor_users auditor_users_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY auditor_users
    ADD CONSTRAINT auditor_users_pkey PRIMARY KEY (email_address);


--
-- TOC entry 3128 (class 2606 OID 16628)
-- Name: aws_accounts aws_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_accounts
    ADD CONSTRAINT aws_accounts_pkey PRIMARY KEY (aws_account_id);


--
-- TOC entry 3126 (class 2606 OID 16592)
-- Name: aws_cross_account_roles aws_cross_account_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_cross_account_roles
    ADD CONSTRAINT aws_cross_account_roles_pkey PRIMARY KEY (role_arn);


--
-- TOC entry 3139 (class 2606 OID 27318)
-- Name: cht_aws_users cht_aws_users_pkey; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY cht_aws_users
    ADD CONSTRAINT cht_aws_users_pkey PRIMARY KEY (insert_id);


--
-- TOC entry 3141 (class 2606 OID 27357)
-- Name: al_accounts pk_al_account_id; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY al_accounts
    ADD CONSTRAINT pk_al_account_id PRIMARY KEY (al_account_id);


--
-- TOC entry 3111 (class 2606 OID 16414)
-- Name: cht_aws_instances pk_cht_aws_instances; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY cht_aws_instances
    ADD CONSTRAINT pk_cht_aws_instances PRIMARY KEY (cht_aws_instance_id);


--
-- TOC entry 3136 (class 2606 OID 17065)
-- Name: cht_instances pk_cht_instance_insert_id; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY cht_instances
    ADD CONSTRAINT pk_cht_instance_insert_id PRIMARY KEY (cht_instance_insert_id);


--
-- TOC entry 3133 (class 2606 OID 16997)
-- Name: aud_tags pk_tag_insert_id; Type: CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aud_tags
    ADD CONSTRAINT pk_tag_insert_id PRIMARY KEY (tag_insert_id);


--
-- TOC entry 3119 (class 1259 OID 34188)
-- Name: aud_iam_groups_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX aud_iam_groups_insert_ts_idx ON aud_iam_groups USING btree (insert_ts DESC);


--
-- TOC entry 3122 (class 1259 OID 34190)
-- Name: aud_iam_policies_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX aud_iam_policies_insert_ts_idx ON aud_iam_policies USING btree (insert_ts DESC);


--
-- TOC entry 3116 (class 1259 OID 34189)
-- Name: aud_iam_roles_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX aud_iam_roles_insert_ts_idx ON aud_iam_roles USING btree (insert_ts DESC);


--
-- TOC entry 3142 (class 1259 OID 35017)
-- Name: audit_users_and_policies_arn_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_arn_idx ON audit_users_and_policies USING btree (arn);


--
-- TOC entry 3143 (class 1259 OID 35016)
-- Name: audit_users_and_policies_aws_account_id_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_aws_account_id_idx ON audit_users_and_policies USING btree (aws_account_id);


--
-- TOC entry 3144 (class 1259 OID 35015)
-- Name: audit_users_and_policies_aws_account_name_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_aws_account_name_idx ON audit_users_and_policies USING btree (aws_account_name);


--
-- TOC entry 3145 (class 1259 OID 35018)
-- Name: audit_users_and_policies_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_insert_ts_idx ON audit_users_and_policies USING btree (insert_ts);


--
-- TOC entry 3146 (class 1259 OID 35022)
-- Name: audit_users_and_policies_policy_document_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_policy_document_idx ON audit_users_and_policies USING gin (policy_document);


--
-- TOC entry 3147 (class 1259 OID 35021)
-- Name: audit_users_and_policies_policyarn_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_policyarn_idx ON audit_users_and_policies USING btree (policyarn);


--
-- TOC entry 3148 (class 1259 OID 35020)
-- Name: audit_users_and_policies_policyname_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_policyname_idx ON audit_users_and_policies USING btree (policyname);


--
-- TOC entry 3149 (class 1259 OID 35019)
-- Name: audit_users_and_policies_username_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX audit_users_and_policies_username_idx ON audit_users_and_policies USING btree (username);


--
-- TOC entry 3137 (class 1259 OID 34191)
-- Name: cht_aws_users_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX cht_aws_users_insert_ts_idx ON cht_aws_users USING btree (insert_ts DESC);


--
-- TOC entry 3134 (class 1259 OID 34192)
-- Name: cht_instances_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX cht_instances_insert_ts_idx ON cht_instances USING btree (insert_ts DESC);


--
-- TOC entry 3131 (class 1259 OID 34193)
-- Name: cht_vpcs_insert_ts_idx; Type: INDEX; Schema: public; Owner: isodbadmin
--

CREATE INDEX cht_vpcs_insert_ts_idx ON cht_vpcs USING btree (insert_ts DESC);


--
-- TOC entry 3272 (class 2618 OID 27332)
-- Name: view_account_overview _RETURN; Type: RULE; Schema: public; Owner: isodbadmin
--

CREATE RULE "_RETURN" AS
    ON SELECT TO view_account_overview DO INSTEAD  SELECT a.aws_account_name,
    a.aws_account_id,
    a.account_active,
    count(c.*) AS "AWS Instance Count (CHT)"
   FROM aws_accounts a,
    cht_instances c
  WHERE ((c.insert_ts <= (now() - '1 day'::interval)) AND (a.aws_account_id = c.aws_account_id))
  GROUP BY a.aws_account_id
  ORDER BY a.aws_account_id;


--
-- TOC entry 3151 (class 2606 OID 16648)
-- Name: aws_accounts_to_auditor_users fk_auditor_user_email; Type: FK CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_accounts_to_auditor_users
    ADD CONSTRAINT fk_auditor_user_email FOREIGN KEY (email_address) REFERENCES auditor_users(email_address) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3150 (class 2606 OID 16643)
-- Name: aws_accounts_to_auditor_users fk_aws_account_id; Type: FK CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_accounts_to_auditor_users
    ADD CONSTRAINT fk_aws_account_id FOREIGN KEY (aws_account_id) REFERENCES aws_accounts(aws_account_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3153 (class 2606 OID 16666)
-- Name: aws_account_roles fk_aws_account_roles_account_id; Type: FK CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_account_roles
    ADD CONSTRAINT fk_aws_account_roles_account_id FOREIGN KEY (aws_account_id) REFERENCES aws_accounts(aws_account_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3152 (class 2606 OID 16661)
-- Name: aws_account_roles fk_aws_account_roles_email; Type: FK CONSTRAINT; Schema: public; Owner: isodbadmin
--

ALTER TABLE ONLY aws_account_roles
    ADD CONSTRAINT fk_aws_account_roles_email FOREIGN KEY (email_address) REFERENCES auditor_users(email_address) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- TOC entry 3286 (class 0 OID 0)
-- Dependencies: 3
-- Name: public; Type: ACL; Schema: -; Owner: isodbadmin
--

REVOKE ALL ON SCHEMA public FROM rdsadmin;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO isodbadmin;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT USAGE ON SCHEMA public TO php_readonly;


--
-- TOC entry 3288 (class 0 OID 0)
-- Dependencies: 220
-- Name: al_account_keys; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE al_account_keys TO php_readonly;


--
-- TOC entry 3290 (class 0 OID 0)
-- Dependencies: 219
-- Name: al_accounts; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE al_accounts TO php_readonly;


--
-- TOC entry 3292 (class 0 OID 0)
-- Dependencies: 217
-- Name: al_overview; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE al_overview TO php_readonly;


--
-- TOC entry 3293 (class 0 OID 0)
-- Dependencies: 190
-- Name: al_remediations; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT ALL ON TABLE al_remediations TO srv_iso;
GRANT SELECT ON TABLE al_remediations TO php_readonly;


--
-- TOC entry 3295 (class 0 OID 0)
-- Dependencies: 189
-- Name: al_remediations_al_remediation_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE al_remediations_al_remediation_id_seq TO php_readonly;


--
-- TOC entry 3297 (class 0 OID 0)
-- Dependencies: 210
-- Name: aud_aws_instances; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_aws_instances TO php_readonly;


--
-- TOC entry 3298 (class 0 OID 0)
-- Dependencies: 193
-- Name: aud_iam_group_details_aud_iam_group_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE aud_iam_group_details_aud_iam_group_id_seq TO php_readonly;


--
-- TOC entry 3299 (class 0 OID 0)
-- Dependencies: 194
-- Name: aud_iam_groups; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_iam_groups TO php_readonly;


--
-- TOC entry 3300 (class 0 OID 0)
-- Dependencies: 198
-- Name: aud_iam_policies_aud_iam_policies_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE aud_iam_policies_aud_iam_policies_id_seq TO php_readonly;


--
-- TOC entry 3301 (class 0 OID 0)
-- Dependencies: 199
-- Name: aud_iam_policies; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_iam_policies TO php_readonly;


--
-- TOC entry 3302 (class 0 OID 0)
-- Dependencies: 197
-- Name: aud_iam_policy_details_aud_iam_policy_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE aud_iam_policy_details_aud_iam_policy_id_seq TO php_readonly;


--
-- TOC entry 3303 (class 0 OID 0)
-- Dependencies: 192
-- Name: aud_iam_roles; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_iam_roles TO php_readonly;


--
-- TOC entry 3305 (class 0 OID 0)
-- Dependencies: 191
-- Name: aud_iam_role_details_aud_iam_role_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE aud_iam_role_details_aud_iam_role_id_seq TO php_readonly;


--
-- TOC entry 3306 (class 0 OID 0)
-- Dependencies: 195
-- Name: aud_iam_user_details_aud_iam_user_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE aud_iam_user_details_aud_iam_user_id_seq TO php_readonly;


--
-- TOC entry 3307 (class 0 OID 0)
-- Dependencies: 196
-- Name: aud_iam_users; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_iam_users TO php_readonly;


--
-- TOC entry 3309 (class 0 OID 0)
-- Dependencies: 209
-- Name: aud_tags; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aud_tags TO php_readonly;


--
-- TOC entry 3311 (class 0 OID 0)
-- Dependencies: 226
-- Name: audit_users_and_policies; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE audit_users_and_policies TO php_readonly;


--
-- TOC entry 3313 (class 0 OID 0)
-- Dependencies: 202
-- Name: auditor_users; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE auditor_users TO php_readonly;


--
-- TOC entry 3315 (class 0 OID 0)
-- Dependencies: 204
-- Name: aws_account_roles; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aws_account_roles TO php_readonly;


--
-- TOC entry 3316 (class 0 OID 0)
-- Dependencies: 201
-- Name: aws_accounts; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aws_accounts TO php_readonly;


--
-- TOC entry 3317 (class 0 OID 0)
-- Dependencies: 218
-- Name: aws_accounts_al_accounts; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aws_accounts_al_accounts TO php_readonly;


--
-- TOC entry 3318 (class 0 OID 0)
-- Dependencies: 203
-- Name: aws_accounts_to_auditor_users; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aws_accounts_to_auditor_users TO php_readonly;


--
-- TOC entry 3320 (class 0 OID 0)
-- Dependencies: 200
-- Name: aws_cross_account_roles; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE aws_cross_account_roles TO php_readonly;


--
-- TOC entry 3322 (class 0 OID 0)
-- Dependencies: 187
-- Name: cht_aws_instances; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE cht_aws_instances TO php_readonly;


--
-- TOC entry 3324 (class 0 OID 0)
-- Dependencies: 188
-- Name: cht_aws_instances_cht_aws_instance_id_seq; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON SEQUENCE cht_aws_instances_cht_aws_instance_id_seq TO php_readonly;


--
-- TOC entry 3325 (class 0 OID 0)
-- Dependencies: 215
-- Name: cht_aws_users; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE cht_aws_users TO php_readonly;


--
-- TOC entry 3327 (class 0 OID 0)
-- Dependencies: 213
-- Name: cht_instances; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE cht_instances TO php_readonly;


--
-- TOC entry 3329 (class 0 OID 0)
-- Dependencies: 206
-- Name: cht_subnets; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE cht_subnets TO php_readonly;


--
-- TOC entry 3331 (class 0 OID 0)
-- Dependencies: 207
-- Name: cht_vpcs; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE cht_vpcs TO php_readonly;


--
-- TOC entry 3333 (class 0 OID 0)
-- Dependencies: 205
-- Name: neteng_ip_allocation; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE neteng_ip_allocation TO php_readonly;


--
-- TOC entry 3334 (class 0 OID 0)
-- Dependencies: 216
-- Name: view_account_overview; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_account_overview TO php_readonly;


--
-- TOC entry 3335 (class 0 OID 0)
-- Dependencies: 224
-- Name: view_al_install_summary; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_al_install_summary TO php_readonly;


--
-- TOC entry 3336 (class 0 OID 0)
-- Dependencies: 223
-- Name: view_al_status; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_al_status TO php_readonly;


--
-- TOC entry 3337 (class 0 OID 0)
-- Dependencies: 228
-- Name: view_audit_policy_map; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_audit_policy_map TO php_readonly;


--
-- TOC entry 3338 (class 0 OID 0)
-- Dependencies: 227
-- Name: view_audit_users; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_audit_users TO php_readonly;


--
-- TOC entry 3340 (class 0 OID 0)
-- Dependencies: 221
-- Name: view_aws_accounts_not_in_cht; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_aws_accounts_not_in_cht TO php_readonly;


--
-- TOC entry 3341 (class 0 OID 0)
-- Dependencies: 211
-- Name: view_aws_instance_tags_last_24_hours; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_aws_instance_tags_last_24_hours TO php_readonly;


--
-- TOC entry 3343 (class 0 OID 0)
-- Dependencies: 225
-- Name: view_cloud_audit_review; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_cloud_audit_review TO php_readonly;


--
-- TOC entry 3345 (class 0 OID 0)
-- Dependencies: 222
-- Name: view_iam_policy_statement; Type: ACL; Schema: public; Owner: isodbadmin
--

GRANT SELECT ON TABLE view_iam_policy_statement TO php_readonly;


--
-- TOC entry 1818 (class 826 OID 16618)
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: isodbadmin
--

ALTER DEFAULT PRIVILEGES FOR ROLE isodbadmin IN SCHEMA public GRANT SELECT ON TABLES  TO php_readonly;


-- Completed on 2017-04-24 14:58:50 EDT

--
-- PostgreSQL database dump complete
--

