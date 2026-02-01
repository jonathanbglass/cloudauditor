-- CloudAuditor Modern Database Schema
-- For Resource Discovery Engine
-- Database: cloudauditor

-- Main resources table for all discovered AWS resources
CREATE TABLE IF NOT EXISTS public.resources (
    id BIGSERIAL PRIMARY KEY,
    resource_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_arn TEXT,
    region TEXT NOT NULL,
    account_id TEXT NOT NULL,
    name TEXT,
    tags JSONB,
    properties JSONB NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(resource_id, resource_type, region, account_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_resources_type ON public.resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_resources_region ON public.resources(region);
CREATE INDEX IF NOT EXISTS idx_resources_account ON public.resources(account_id);
CREATE INDEX IF NOT EXISTS idx_resources_discovered ON public.resources(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_resources_arn ON public.resources(resource_arn);
CREATE INDEX IF NOT EXISTS idx_resources_tags ON public.resources USING GIN (tags);

-- Resource relationships table
CREATE TABLE IF NOT EXISTS public.resource_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_resource_id BIGINT NOT NULL REFERENCES public.resources(id) ON DELETE CASCADE,
    target_resource_id BIGINT NOT NULL REFERENCES public.resources(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(source_resource_id, target_resource_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_relationships_source ON public.resource_relationships(source_resource_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON public.resource_relationships(target_resource_id);

-- Discovery runs table to track execution history
CREATE TABLE IF NOT EXISTS public.discovery_runs (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'running',
    total_resources INTEGER DEFAULT 0,
    resource_types INTEGER DEFAULT 0,
    errors JSONB,
    duration_seconds DECIMAL(10,2)
);

CREATE INDEX IF NOT EXISTS idx_discovery_runs_started ON public.discovery_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_discovery_runs_status ON public.discovery_runs(status);

-- Comments for documentation
COMMENT ON TABLE public.resources IS 'Stores all discovered AWS resources from Resource Explorer, Config, and Cloud Control APIs';
COMMENT ON TABLE public.resource_relationships IS 'Tracks relationships between AWS resources (e.g., EC2 instance -> VPC)';
COMMENT ON TABLE public.discovery_runs IS 'Tracks resource discovery execution history and metrics';

COMMENT ON COLUMN public.resources.properties IS 'Full JSON representation of the resource from AWS API';
COMMENT ON COLUMN public.resources.tags IS 'Resource tags as JSON key-value pairs';
COMMENT ON COLUMN public.resources.last_seen_at IS 'Last time this resource was seen during discovery (for detecting deleted resources)';
