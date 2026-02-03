-- Database: isodb

-- DROP DATABASE isodb;

CREATE DATABASE isodb
    WITH 
    OWNER = isodbadmin
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- User: php_readonly
-- DROP USER php_readonly;

CREATE USER php_readonly WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION;

-- User: isodbadmin
-- DROP USER isodbadmin;

CREATE USER isodbadmin WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  CREATEDB
  CREATEROLE
  NOREPLICATION
  VALID UNTIL 'infinity'

GRANT rds_superuser TO isodbadmin;

-- Table: public.aud_iam_groups

-- DROP TABLE public.aud_iam_groups;

CREATE TABLE public.aud_iam_groups
(
      group_insert_ts timestamp with time zone NOT NULL DEFAULT now(),
      aud_iam_group_json jsonb,
      aud_iam_group_id bigint NOT NULL DEFAULT nextval('aud_iam_group_details_aud_iam_group_id_seq'::regclass),
      "Arn" text COLLATE pg_catalog."default",
      "GroupId" text COLLATE pg_catalog."default",
      "Path" text COLLATE pg_catalog."default",
      "CreateDate" timestamp with time zone,
      "GroupName" text COLLATE pg_catalog."default",
      aws_account_id bigint NOT NULL,
      CONSTRAINT aud_iam_group_details_pkey PRIMARY KEY (aud_iam_group_id)
)
WITH ( OIDS = FALSE) TABLESPACE pg_default;
ALTER TABLE public.aud_iam_groups OWNER to isodbadmin;

-- Table: public.aud_iam_policies

-- DROP TABLE public.aud_iam_policies;

CREATE TABLE public.aud_iam_policies
(
      aud_iam_policy_ts timestamp with time zone NOT NULL,
      aud_iam_policy_json jsonb,
      aud_iam_policies_id bigint NOT NULL DEFAULT nextval('aud_iam_policies_aud_iam_policies_id_seq'::regclass),
      aud_iam_policy_arn text COLLATE pg_catalog."default",
      "aud_iam_policy_Path" text COLLATE pg_catalog."default",
      "aud_iam_policy_CreateDate" timestamp with time zone,
      "aud_iam_policy_PolicyName" text COLLATE pg_catalog."default",
      aws_account_id bigint NOT NULL,
      "aud_iam_policy_AttachmentCount" integer,
      "aud_iam_policy_IsAttachable" boolean NOT NULL,
      "aud_iam_policy_DefaultVersionId" text COLLATE pg_catalog."default",
      "aud_iam_policy_UpdateDate" timestamp without time zone,
      last_audited timestamp with time zone NOT NULL DEFAULT now(),
      "aud_iam_PolicyId" text COLLATE pg_catalog."default" NOT NULL,
      CONSTRAINT aud_iam_policies_pkey PRIMARY KEY (aud_iam_policies_id)
)
WITH ( OIDS = FALSE) TABLESPACE pg_default;

ALTER TABLE public.aud_iam_policies OWNER to isodbadmin;

-- Table: public.aud_iam_roles

-- DROP TABLE public.aud_iam_roles;

CREATE TABLE public.aud_iam_roles
(
      role_insert_ts timestamp with time zone NOT NULL DEFAULT now(),
      aud_iam_role_json jsonb,
      aud_iam_role_id bigint NOT NULL DEFAULT nextval('aud_iam_role_details_aud_iam_role_id_seq'::regclass),
      "Arn" text COLLATE pg_catalog."default",
      "RoleId" text COLLATE pg_catalog."default",
      "Path" text COLLATE pg_catalog."default",
      "CreateDate" timestamp with time zone,
      "RoleName" text COLLATE pg_catalog."default",
      aws_account_id bigint NOT NULL,
      "AssumeRolePolicyDocument" jsonb,
      CONSTRAINT aud_iam_role_details_pkey PRIMARY KEY (aud_iam_role_id)
)
WITH ( OIDS = FALSE) TABLESPACE pg_default;

ALTER TABLE public.aud_iam_roles OWNER to isodbadmin;

-- Table: public.aud_iam_users

-- DROP TABLE public.aud_iam_users;

CREATE TABLE public.aud_iam_users
(
      user_insert_ts timestamp with time zone NOT NULL DEFAULT now(),
      aud_iam_user_json jsonb,
      aud_iam_user_id bigint NOT NULL DEFAULT nextval('aud_iam_user_details_aud_iam_user_id_seq'::regclass),
      "Arn" text COLLATE pg_catalog."default",
      "UserId" text COLLATE pg_catalog."default",
      "Path" text COLLATE pg_catalog."default",
      "CreateDate" timestamp with time zone,
      "UserName" text COLLATE pg_catalog."default",
      aws_account_id bigint NOT NULL,
      "PasswordLastUsed" timestamp with time zone,
      CONSTRAINT aud_iam_user_details_pkey PRIMARY KEY (aud_iam_user_id)
)
WITH ( OIDS = FALSE) TABLESPACE pg_default;

ALTER TABLE public.aud_iam_users OWNER to isodbadmin;

-- Table: public.aws_cross_account_roles

-- DROP TABLE public.aws_cross_account_roles;

CREATE TABLE public.aws_cross_account_roles
(
      aws_account_id bigint NOT NULL,
      role_arn text COLLATE pg_catalog."default" NOT NULL,
      working boolean,
      inserted_ts timestamp with time zone NOT NULL,
      last_used_ts timestamp with time zone,
      CONSTRAINT aws_cross_account_roles_pkey PRIMARY KEY (role_arn)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.aws_cross_account_roles
   OWNER to isodbadmin;

GRANT ALL ON TABLE public.aws_cross_account_roles TO isodbadmin;

GRANT SELECT ON TABLE public.aws_cross_account_roles TO php_readonly;

COMMENT ON TABLE public.aws_cross_account_roles
    IS 'A table to collect cross account roles in the various AWS accounts.  At a mininum it needs Account Number + Role ARN.  It may also need a Record Insert TimeStamp for compliance tracking, and maybe a column for "Is it Working?" and "Last Used Timestamp".  That way we can track broken roles.';

-- Table: public.aud_tags

-- DROP TABLE public.aud_tags;

CREATE TABLE public.aud_tags
(
      aws_account_id bigint NOT NULL,
          insert_ts timestamp with time zone NOT NULL DEFAULT now(),
              resourcetype character(50) COLLATE pg_catalog."default" NOT NULL,
                  resourceid character(50) COLLATE pg_catalog."default" NOT NULL,
                      tagkey character(128) COLLATE pg_catalog."default" NOT NULL,
                          tag_insert_id bigint NOT NULL DEFAULT nextval('aud_tags_tag_insert_id_seq'::regclass),
                              tagvalue character(256) COLLATE pg_catalog."default" NOT NULL,
                                  CONSTRAINT pk_tag_insert_id PRIMARY KEY (tag_insert_id)
                                )
                                WITH (
                                      OIDS = FALSE
                                    )
                                    TABLESPACE pg_default;

                                    ALTER TABLE public.aud_tags
                                        OWNER to isodbadmin;

                                        GRANT ALL ON TABLE public.aud_tags TO isodbadmin;

                                        GRANT SELECT ON TABLE public.aud_tags TO php_readonly;

                                        COMMENT ON TABLE public.aud_tags
                                            IS 'table to store output from boto3 ec2 describe_tags';

-- Table: public.aud_aws_instances

-- DROP TABLE public.aud_aws_instances;

CREATE TABLE public.aud_aws_instances
(
      aws_account_id bigint NOT NULL,
          insert_ts timestamp with time zone NOT NULL DEFAULT now(),
              instance_json jsonb NOT NULL,
                  instanceid character(50) COLLATE pg_catalog."default" NOT NULL
                )
                WITH (
                      OIDS = FALSE
                    )
                    TABLESPACE pg_default;

                    ALTER TABLE public.aud_aws_instances
                        OWNER to isodbadmin;

                        GRANT ALL ON TABLE public.aud_aws_instances TO isodbadmin;

                        GRANT SELECT ON TABLE public.aud_aws_instances TO php_readonly;

                        COMMENT ON TABLE public.aud_aws_instances
                            IS 'table to store results from ec2 describe_instances; ';
