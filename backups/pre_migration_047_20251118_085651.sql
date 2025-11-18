--
-- PostgreSQL database dump
--

\restrict itLV1kRi1oSNnEyxAeUcFTKQNdCTnp4nTdA9Jb5S83hTIlqliGjGjc7BicgJhKv

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: check_device_health_alerts(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.check_device_health_alerts(p_device_id integer) RETURNS TABLE(alert_type character varying, severity character varying, message text, value numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_latest RECORD;
BEGIN
  -- Get latest metrics
  SELECT * INTO v_latest
  FROM get_latest_device_health(p_device_id);

  -- CPU alert
  IF v_latest.cpu_usage > 90 THEN
    RETURN QUERY SELECT 'cpu'::VARCHAR, 'critical'::VARCHAR,
      'CPU usage critically high'::TEXT, v_latest.cpu_usage;
  ELSIF v_latest.cpu_usage > 80 THEN
    RETURN QUERY SELECT 'cpu'::VARCHAR, 'warning'::VARCHAR,
      'CPU usage high'::TEXT, v_latest.cpu_usage;
  END IF;

  -- Memory alert
  IF v_latest.memory_usage > 90 THEN
    RETURN QUERY SELECT 'memory'::VARCHAR, 'critical'::VARCHAR,
      'Memory usage critically high'::TEXT, v_latest.memory_usage;
  ELSIF v_latest.memory_usage > 80 THEN
    RETURN QUERY SELECT 'memory'::VARCHAR, 'warning'::VARCHAR,
      'Memory usage high'::TEXT, v_latest.memory_usage;
  END IF;

  -- Disk alert
  IF v_latest.disk_usage > 95 THEN
    RETURN QUERY SELECT 'disk'::VARCHAR, 'critical'::VARCHAR,
      'Disk space critically low'::TEXT, v_latest.disk_usage;
  ELSIF v_latest.disk_usage > 85 THEN
    RETURN QUERY SELECT 'disk'::VARCHAR, 'warning'::VARCHAR,
      'Disk space low'::TEXT, v_latest.disk_usage;
  END IF;

  -- Temperature alert
  IF v_latest.temperature > 85 THEN
    RETURN QUERY SELECT 'temperature'::VARCHAR, 'critical'::VARCHAR,
      'Temperature critically high'::TEXT, v_latest.temperature;
  ELSIF v_latest.temperature > 75 THEN
    RETURN QUERY SELECT 'temperature'::VARCHAR, 'warning'::VARCHAR,
      'Temperature high'::TEXT, v_latest.temperature;
  END IF;

  -- Network alert
  IF v_latest.network_status = 'offline' THEN
    RETURN QUERY SELECT 'network'::VARCHAR, 'critical'::VARCHAR,
      'Device offline'::TEXT, 0::DECIMAL;
  ELSIF v_latest.network_status = 'unstable' THEN
    RETURN QUERY SELECT 'network'::VARCHAR, 'warning'::VARCHAR,
      'Network connection unstable'::TEXT, 0::DECIMAL;
  END IF;

  -- Latency alert
  IF v_latest.latency > 1000 THEN
    RETURN QUERY SELECT 'latency'::VARCHAR, 'warning'::VARCHAR,
      'High network latency'::TEXT, v_latest.latency::DECIMAL;
  END IF;
END;
$$;


ALTER FUNCTION public.check_device_health_alerts(p_device_id integer) OWNER TO signage_user;

--
-- Name: cleanup_expired_sessions(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.cleanup_expired_sessions() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW() - INTERVAL '30 days'; -- Keep for 30 days after expiration for audit

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;


ALTER FUNCTION public.cleanup_expired_sessions() OWNER TO signage_user;

--
-- Name: FUNCTION cleanup_expired_sessions(); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.cleanup_expired_sessions() IS 'Delete expired sessions older than 30 days (run as cron job)';


--
-- Name: cleanup_old_health_metrics(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.cleanup_old_health_metrics() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  DELETE FROM device_health_metrics
  WHERE recorded_at < NOW() - INTERVAL '30 days';

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

  RETURN v_deleted_count;
END;
$$;


ALTER FUNCTION public.cleanup_old_health_metrics() OWNER TO signage_user;

--
-- Name: get_child_groups(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_child_groups(p_group_id integer) RETURNS TABLE(group_id integer, depth integer)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE group_tree AS (
        -- Base case: the group itself
        SELECT id, 0 as depth
        FROM device_groups
        WHERE id = p_group_id

        UNION ALL

        -- Recursive case: child groups
        SELECT dg.id, gt.depth + 1
        FROM device_groups dg
        INNER JOIN group_tree gt ON dg.parent_group_id = gt.id
        WHERE dg.deleted_at IS NULL
    )
    SELECT id, depth FROM group_tree;
END;
$$;


ALTER FUNCTION public.get_child_groups(p_group_id integer) OWNER TO signage_user;

--
-- Name: FUNCTION get_child_groups(p_group_id integer); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.get_child_groups(p_group_id integer) IS 'Returns all child groups recursively (including the group itself)';


--
-- Name: get_device_health_average(integer, integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_device_health_average(p_device_id integer, p_hours integer DEFAULT 24) RETURNS TABLE(avg_cpu numeric, avg_memory numeric, avg_disk numeric, avg_temp numeric, avg_latency numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    ROUND(AVG(dhm.cpu_usage), 2),
    ROUND(AVG(dhm.memory_usage), 2),
    ROUND(AVG(dhm.disk_usage), 2),
    ROUND(AVG(dhm.temperature), 2),
    ROUND(AVG(dhm.latency), 2)
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
    AND dhm.recorded_at >= NOW() - (p_hours || ' hours')::INTERVAL;
END;
$$;


ALTER FUNCTION public.get_device_health_average(p_device_id integer, p_hours integer) OWNER TO signage_user;

--
-- Name: get_device_health_history(integer, integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_device_health_history(p_device_id integer, p_hours integer DEFAULT 24) RETURNS TABLE(cpu_usage numeric, memory_usage numeric, disk_usage numeric, temperature numeric, latency integer, recorded_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    dhm.cpu_usage,
    dhm.memory_usage,
    dhm.disk_usage,
    dhm.temperature,
    dhm.latency,
    dhm.recorded_at
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
    AND dhm.recorded_at >= NOW() - (p_hours || ' hours')::INTERVAL
  ORDER BY dhm.recorded_at ASC;
END;
$$;


ALTER FUNCTION public.get_device_health_history(p_device_id integer, p_hours integer) OWNER TO signage_user;

--
-- Name: get_devices_in_group(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_devices_in_group(p_group_id integer) RETURNS TABLE(device_id integer)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT dgm.device_id
    FROM device_group_members dgm
    WHERE dgm.group_id IN (
        SELECT group_id FROM get_child_groups(p_group_id)
    );
END;
$$;


ALTER FUNCTION public.get_devices_in_group(p_group_id integer) OWNER TO signage_user;

--
-- Name: FUNCTION get_devices_in_group(p_group_id integer); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.get_devices_in_group(p_group_id integer) IS 'Returns all devices in a group and its child groups';


--
-- Name: get_group_path(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_group_path(p_group_id integer) RETURNS text
    LANGUAGE plpgsql STABLE
    AS $$
DECLARE
    v_path TEXT;
BEGIN
    WITH RECURSIVE group_path AS (
        -- Base case: the group itself
        SELECT id, name, parent_group_id, ARRAY[name] as path
        FROM device_groups
        WHERE id = p_group_id

        UNION ALL

        -- Recursive case: parent groups
        SELECT dg.id, dg.name, dg.parent_group_id, dg.name || gp.path
        FROM device_groups dg
        INNER JOIN group_path gp ON gp.parent_group_id = dg.id
    )
    SELECT array_to_string(path, ' > ')
    INTO v_path
    FROM group_path
    WHERE parent_group_id IS NULL;

    RETURN v_path;
END;
$$;


ALTER FUNCTION public.get_group_path(p_group_id integer) OWNER TO signage_user;

--
-- Name: FUNCTION get_group_path(p_group_id integer); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.get_group_path(p_group_id integer) IS 'Returns breadcrumb path: "Hotel A > Floor 1 > Lobby"';


--
-- Name: get_latest_device_health(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.get_latest_device_health(p_device_id integer) RETURNS TABLE(cpu_usage numeric, memory_usage numeric, disk_usage numeric, temperature numeric, network_status character varying, latency integer, display_status character varying, recorded_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
  RETURN QUERY
  SELECT
    dhm.cpu_usage,
    dhm.memory_usage,
    dhm.disk_usage,
    dhm.temperature,
    dhm.network_status,
    dhm.latency,
    dhm.display_status,
    dhm.recorded_at
  FROM device_health_metrics dhm
  WHERE dhm.device_id = p_device_id
  ORDER BY dhm.recorded_at DESC
  LIMIT 1;
END;
$$;


ALTER FUNCTION public.get_latest_device_health(p_device_id integer) OWNER TO signage_user;

--
-- Name: refresh_organization_health_summary(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.refresh_organization_health_summary() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_organization_health_summary;
END;
$$;


ALTER FUNCTION public.refresh_organization_health_summary() OWNER TO signage_user;

--
-- Name: revoke_all_user_sessions(integer); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.revoke_all_user_sessions(p_user_id integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    revoked_count INTEGER;
BEGIN
    UPDATE user_sessions
    SET revoked_at = NOW()
    WHERE user_id = p_user_id
      AND revoked_at IS NULL;

    GET DIAGNOSTICS revoked_count = ROW_COUNT;
    RETURN revoked_count;
END;
$$;


ALTER FUNCTION public.revoke_all_user_sessions(p_user_id integer) OWNER TO signage_user;

--
-- Name: FUNCTION revoke_all_user_sessions(p_user_id integer); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.revoke_all_user_sessions(p_user_id integer) IS 'Revoke all sessions for user (logout all devices)';


--
-- Name: revoke_session(character varying); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.revoke_session(p_session_token character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE user_sessions
    SET revoked_at = NOW()
    WHERE session_token = p_session_token
      AND revoked_at IS NULL;

    RETURN FOUND;
END;
$$;


ALTER FUNCTION public.revoke_session(p_session_token character varying) OWNER TO signage_user;

--
-- Name: FUNCTION revoke_session(p_session_token character varying); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.revoke_session(p_session_token character varying) IS 'Revoke session by token (manual logout)';


--
-- Name: update_pms_updated_at(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_pms_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_pms_updated_at() OWNER TO signage_user;

--
-- Name: update_schedules_updated_at(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_schedules_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_schedules_updated_at() OWNER TO signage_user;

--
-- Name: update_session_activity(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_session_activity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.last_activity := NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_session_activity() OWNER TO signage_user;

--
-- Name: FUNCTION update_session_activity(); Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON FUNCTION public.update_session_activity() IS 'Auto-update last_activity timestamp when session is verified';


--
-- Name: update_templates_updated_at(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_templates_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_templates_updated_at() OWNER TO signage_user;

--
-- Name: update_translations_updated_at(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_translations_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_translations_updated_at() OWNER TO signage_user;

--
-- Name: update_widgets_updated_at(); Type: FUNCTION; Schema: public; Owner: signage_user
--

CREATE FUNCTION public.update_widgets_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_widgets_updated_at() OWNER TO signage_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    organization_id integer,
    action character varying(100) NOT NULL,
    resource_type character varying(50) NOT NULL,
    resource_id integer,
    details json,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO signage_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO signage_user;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: content_assignments; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.content_assignments (
    id integer NOT NULL,
    device_id integer,
    content_id integer NOT NULL,
    priority integer DEFAULT 1 NOT NULL,
    schedule jsonb,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    assigned_by_id integer,
    expires_at timestamp with time zone,
    organization_id integer NOT NULL,
    tag_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    CONSTRAINT content_assignments_target_check CHECK ((((device_id IS NOT NULL) AND (tag_id IS NULL)) OR ((device_id IS NULL) AND (tag_id IS NOT NULL))))
);


ALTER TABLE public.content_assignments OWNER TO signage_user;

--
-- Name: TABLE content_assignments; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.content_assignments IS 'Content assignments to devices or tags - supports direct and tag-based assignment methods';


--
-- Name: COLUMN content_assignments.device_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.device_id IS 'Direct device assignment (Method 1 - mutually exclusive with tag_id)';


--
-- Name: COLUMN content_assignments.content_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.content_id IS 'Content to be assigned';


--
-- Name: COLUMN content_assignments.priority; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.priority IS 'Display priority (lower number = higher priority)';


--
-- Name: COLUMN content_assignments.schedule; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.schedule IS 'Optional schedule configuration (JSONB)';


--
-- Name: COLUMN content_assignments.assigned_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.assigned_at IS 'When assignment was created';


--
-- Name: COLUMN content_assignments.assigned_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.assigned_by_id IS 'User who created the assignment';


--
-- Name: COLUMN content_assignments.expires_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.expires_at IS 'Optional expiration date for temporary assignments';


--
-- Name: COLUMN content_assignments.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.organization_id IS 'Organization owning this assignment (multi-tenancy)';


--
-- Name: COLUMN content_assignments.tag_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.tag_id IS 'Tag-based assignment (Method 3 - mutually exclusive with device_id)';


--
-- Name: COLUMN content_assignments.created_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.created_at IS 'Record creation timestamp';


--
-- Name: COLUMN content_assignments.updated_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.updated_at IS 'Record last update timestamp';


--
-- Name: content_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.content_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.content_assignments_id_seq OWNER TO signage_user;

--
-- Name: content_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.content_assignments_id_seq OWNED BY public.content_assignments.id;


--
-- Name: content_playback_logs; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.content_playback_logs (
    id integer NOT NULL,
    content_id integer NOT NULL,
    playlist_id integer,
    device_id integer NOT NULL,
    organization_id integer NOT NULL,
    started_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone,
    duration_seconds integer,
    is_completed boolean DEFAULT false NOT NULL,
    skip_reason character varying(50),
    source character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.content_playback_logs OWNER TO signage_user;

--
-- Name: TABLE content_playback_logs; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.content_playback_logs IS 'Content playback tracking for analytics and compliance';


--
-- Name: COLUMN content_playback_logs.duration_seconds; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_playback_logs.duration_seconds IS 'Actual playback duration (may differ from content.duration)';


--
-- Name: COLUMN content_playback_logs.is_completed; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_playback_logs.is_completed IS 'TRUE if content playback completed successfully, FALSE if interrupted or failed';


--
-- Name: COLUMN content_playback_logs.skip_reason; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_playback_logs.skip_reason IS 'Why playback was interrupted (NULL if completed)';


--
-- Name: COLUMN content_playback_logs.source; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_playback_logs.source IS 'How content was assigned: playlist, direct_assignment, tag_assignment';


--
-- Name: contents; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.contents (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    content_type character varying(20) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_url character varying(500) NOT NULL,
    storage_key character varying(255) NOT NULL,
    file_hash character varying(64) NOT NULL,
    duration integer DEFAULT 10 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    file_size bigint NOT NULL,
    mime_type character varying(100) NOT NULL,
    original_filename character varying(255) NOT NULL,
    file_extension character varying(20) NOT NULL,
    resolution character varying(50),
    width integer,
    height integer,
    codec character varying(50),
    fps double precision,
    bitrate integer,
    media_duration double precision,
    video_start_time double precision DEFAULT 0.0 NOT NULL,
    video_end_time double precision,
    audio_codec character varying(50),
    audio_bitrate integer,
    audio_sample_rate integer,
    audio_channels integer DEFAULT 2 NOT NULL,
    transcoding_status character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    transcoding_job_id character varying(200),
    transcoding_progress integer DEFAULT 0 NOT NULL,
    transcoding_error text,
    hls_master_playlist_path character varying(500),
    hls_master_playlist_url character varying(500),
    hls_variants jsonb,
    thumbnail_path character varying(500),
    thumbnail_url character varying(500),
    thumbnail_generated_at timestamp with time zone,
    upload_status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    organization_id integer NOT NULL,
    uploaded_by_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT check_contents_audio_bitrate_positive CHECK (((audio_bitrate IS NULL) OR (audio_bitrate > 0))),
    CONSTRAINT check_contents_bitrate_positive CHECK (((bitrate IS NULL) OR (bitrate > 0))),
    CONSTRAINT check_contents_duration_positive CHECK (((duration IS NULL) OR (duration > 0))),
    CONSTRAINT check_contents_file_size_positive CHECK (((file_size IS NULL) OR (file_size > 0))),
    CONSTRAINT check_contents_height_positive CHECK (((height IS NULL) OR (height > 0))),
    CONSTRAINT check_contents_media_duration_positive CHECK (((media_duration IS NULL) OR (media_duration > (0)::double precision))),
    CONSTRAINT check_contents_transcoding_progress_range CHECK (((transcoding_progress >= 0) AND (transcoding_progress <= 100))),
    CONSTRAINT check_contents_width_positive CHECK (((width IS NULL) OR (width > 0)))
);


ALTER TABLE public.contents OWNER TO signage_user;

--
-- Name: TABLE contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.contents IS 'Content files with custom storage system (images, videos, audio)';


--
-- Name: COLUMN contents.storage_key; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.storage_key IS 'Unique storage path: {type}s/{year}/{month}/org_{id}/{uuid}.{ext}';


--
-- Name: COLUMN contents.file_hash; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.file_hash IS 'SHA256 hash for deduplication within organization';


--
-- Name: COLUMN contents.transcoding_status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.transcoding_status IS 'Status: pending, processing, completed, failed';


--
-- Name: COLUMN contents.hls_variants; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.hls_variants IS 'JSON array of HLS quality variants (e.g., [{"quality": "720p", "path": "..."}])';


--
-- Name: COLUMN contents.upload_status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.upload_status IS 'Status: pending, completed, failed';


--
-- Name: COLUMN contents.uploaded_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.uploaded_by_id IS 'User ID who uploaded this content (FK to users.id)';


--
-- Name: COLUMN contents.updated_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.updated_at IS 'Timestamp when content was last modified (renamed from last_updated)';


--
-- Name: CONSTRAINT check_contents_duration_positive ON contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_contents_duration_positive ON public.contents IS 'Ensures display duration is positive when specified';


--
-- Name: CONSTRAINT check_contents_file_size_positive ON contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_contents_file_size_positive ON public.contents IS 'Ensures file size is positive when specified';


--
-- Name: CONSTRAINT check_contents_media_duration_positive ON contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_contents_media_duration_positive ON public.contents IS 'Ensures media duration (actual length) is positive when specified';


--
-- Name: CONSTRAINT check_contents_transcoding_progress_range ON contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_contents_transcoding_progress_range ON public.contents IS 'Ensures transcoding progress is between 0 and 100 percent';


--
-- Name: content_performance; Type: VIEW; Schema: public; Owner: signage_user
--

CREATE VIEW public.content_performance AS
 SELECT c.id AS content_id,
    c.title,
    c.content_type,
    c.organization_id,
    count(*) AS total_plays,
    count(*) FILTER (WHERE (cpl.is_completed = true)) AS completed_plays,
    round(avg(cpl.duration_seconds), 2) AS avg_duration_seconds,
    max(cpl.started_at) AS last_played_at,
    count(DISTINCT cpl.device_id) AS unique_devices
   FROM (public.contents c
     LEFT JOIN public.content_playback_logs cpl ON ((cpl.content_id = c.id)))
  GROUP BY c.id, c.title, c.content_type, c.organization_id;


ALTER TABLE public.content_performance OWNER TO signage_user;

--
-- Name: VIEW content_performance; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON VIEW public.content_performance IS 'Content playback performance metrics for analytics';


--
-- Name: content_playback_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.content_playback_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.content_playback_logs_id_seq OWNER TO signage_user;

--
-- Name: content_playback_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.content_playback_logs_id_seq OWNED BY public.content_playback_logs.id;


--
-- Name: content_tags; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.content_tags (
    id integer NOT NULL,
    content_id integer NOT NULL,
    tag_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.content_tags OWNER TO signage_user;

--
-- Name: TABLE content_tags; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.content_tags IS 'Many-to-many relationship between contents and tags';


--
-- Name: content_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.content_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.content_tags_id_seq OWNER TO signage_user;

--
-- Name: content_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.content_tags_id_seq OWNED BY public.content_tags.id;


--
-- Name: contents_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.contents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.contents_id_seq OWNER TO signage_user;

--
-- Name: contents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.contents_id_seq OWNED BY public.contents.id;


--
-- Name: device_commands; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_commands (
    id integer NOT NULL,
    device_id integer NOT NULL,
    organization_id integer NOT NULL,
    command_type character varying(50) NOT NULL,
    parameters jsonb,
    reason character varying(200),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    sent_at timestamp with time zone,
    executed_at timestamp with time zone,
    error_message character varying(500),
    created_by_id integer,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    command_data jsonb,
    priority integer DEFAULT 5,
    failed_at timestamp with time zone,
    result jsonb,
    retry_count integer DEFAULT 0,
    max_retries integer DEFAULT 3,
    updated_at timestamp with time zone,
    CONSTRAINT device_commands_command_type_check CHECK (((command_type)::text = ANY ((ARRAY['reset'::character varying, 'refresh'::character varying, 'reload'::character varying, 'speed_test'::character varying, 'update_content'::character varying, 'reboot'::character varying, 'screenshot'::character varying, 'volume'::character varying, 'brightness'::character varying])::text[]))),
    CONSTRAINT device_commands_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'sent'::character varying, 'executed'::character varying, 'failed'::character varying, 'expired'::character varying])::text[])))
);


ALTER TABLE public.device_commands OWNER TO signage_user;

--
-- Name: TABLE device_commands; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_commands IS 'Remote command queue for device management';


--
-- Name: COLUMN device_commands.command_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_commands.command_type IS 'Type of command: reset (clear & reload), refresh (cache clear), reload (page reload), speed_test, update_content, reboot, screenshot, volume, brightness';


--
-- Name: COLUMN device_commands.parameters; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_commands.parameters IS 'JSON parameters for command execution (e.g., {"level": 75} for volume)';


--
-- Name: COLUMN device_commands.status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_commands.status IS 'Command lifecycle: pending → sent → executed/failed/expired';


--
-- Name: COLUMN device_commands.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_commands.created_by_id IS 'User ID who created this command (FK to users.id)';


--
-- Name: COLUMN device_commands.expires_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_commands.expires_at IS 'Command auto-expires after 7 days if not executed';


--
-- Name: device_commands_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_commands_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_commands_id_seq OWNER TO signage_user;

--
-- Name: device_commands_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_commands_id_seq OWNED BY public.device_commands.id;


--
-- Name: device_connection_logs; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_connection_logs (
    id integer NOT NULL,
    device_id integer NOT NULL,
    logged_at timestamp with time zone NOT NULL,
    event_type character varying(50) NOT NULL,
    status character varying(20) NOT NULL,
    latency_ms integer,
    error_message text,
    download_speed_mbps numeric(10,2),
    upload_speed_mbps numeric(10,2),
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    connection_type character varying(20),
    effective_type character varying(10),
    rtt_ms integer,
    endpoint character varying(200),
    http_status integer,
    test_trigger character varying(10),
    test_duration_ms integer,
    CONSTRAINT check_connection_type CHECK (((connection_type IS NULL) OR ((connection_type)::text = ANY ((ARRAY['wifi'::character varying, 'ethernet'::character varying, 'cellular'::character varying, 'bluetooth'::character varying, 'wimax'::character varying, 'other'::character varying, 'none'::character varying, 'unknown'::character varying])::text[])))),
    CONSTRAINT check_effective_type CHECK (((effective_type IS NULL) OR ((effective_type)::text = ANY ((ARRAY['slow-2g'::character varying, '2g'::character varying, '3g'::character varying, '4g'::character varying, '5g'::character varying, 'unknown'::character varying])::text[])))),
    CONSTRAINT check_rtt_ms CHECK (((rtt_ms IS NULL) OR (rtt_ms >= 0))),
    CONSTRAINT check_test_duration_ms CHECK (((test_duration_ms IS NULL) OR (test_duration_ms >= 0))),
    CONSTRAINT check_test_trigger CHECK (((test_trigger IS NULL) OR ((test_trigger)::text = ANY ((ARRAY['auto'::character varying, 'manual'::character varying])::text[])))),
    CONSTRAINT device_connection_logs_download_speed_mbps_check CHECK ((download_speed_mbps >= (0)::numeric)),
    CONSTRAINT device_connection_logs_event_type_check CHECK (((event_type)::text = ANY ((ARRAY['network'::character varying, 'server'::character varying, 'speed_test'::character varying])::text[]))),
    CONSTRAINT device_connection_logs_latency_ms_check CHECK ((latency_ms >= 0)),
    CONSTRAINT device_connection_logs_upload_speed_mbps_check CHECK ((upload_speed_mbps >= (0)::numeric))
);


ALTER TABLE public.device_connection_logs OWNER TO signage_user;

--
-- Name: TABLE device_connection_logs; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_connection_logs IS 'Connection activity logs from player devices - tracks network status, server connectivity, and speed test results';


--
-- Name: COLUMN device_connection_logs.device_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.device_id IS 'Reference to the device that generated this log';


--
-- Name: COLUMN device_connection_logs.logged_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.logged_at IS 'Timestamp when the event occurred on the player device';


--
-- Name: COLUMN device_connection_logs.event_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.event_type IS 'Type of event: network (browser online/offline), server (API connectivity), speed_test (network performance)';


--
-- Name: COLUMN device_connection_logs.status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.status IS 'Event status: online, offline, connected, disconnected, tested';


--
-- Name: COLUMN device_connection_logs.latency_ms; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.latency_ms IS 'Network latency in milliseconds (for server and speed_test events)';


--
-- Name: COLUMN device_connection_logs.error_message; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.error_message IS 'Error details if the event indicates a failure';


--
-- Name: COLUMN device_connection_logs.download_speed_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.download_speed_mbps IS 'Download speed in Mbps (for speed_test events only)';


--
-- Name: COLUMN device_connection_logs.upload_speed_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.upload_speed_mbps IS 'Upload speed in Mbps (for speed_test events only)';


--
-- Name: COLUMN device_connection_logs.metadata; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.metadata IS 'Additional event metadata in JSON format';


--
-- Name: COLUMN device_connection_logs.created_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.created_at IS 'Timestamp when this record was inserted into the database';


--
-- Name: COLUMN device_connection_logs.connection_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.connection_type IS 'Network connection type (wifi, ethernet, cellular, etc)';


--
-- Name: COLUMN device_connection_logs.effective_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.effective_type IS 'Effective network type (4g, 3g, 2g, etc)';


--
-- Name: COLUMN device_connection_logs.rtt_ms; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.rtt_ms IS 'Round-trip time in milliseconds';


--
-- Name: COLUMN device_connection_logs.endpoint; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.endpoint IS 'API endpoint accessed';


--
-- Name: COLUMN device_connection_logs.http_status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.http_status IS 'HTTP status code';


--
-- Name: COLUMN device_connection_logs.test_trigger; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.test_trigger IS 'How speed test was triggered (auto/manual)';


--
-- Name: COLUMN device_connection_logs.test_duration_ms; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.test_duration_ms IS 'Speed test duration in milliseconds';


--
-- Name: device_connection_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

ALTER TABLE public.device_connection_logs ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.device_connection_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: devices; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.devices (
    id integer NOT NULL,
    device_type character varying(20) NOT NULL,
    device_name character varying(200) NOT NULL,
    organization_id integer,
    unique_code character varying(6),
    code_expires_at timestamp with time zone,
    device_uuid character varying(100),
    ip_address character varying(45),
    platform character varying(50),
    screen_width integer,
    screen_height integer,
    viewport_width integer,
    viewport_height integer,
    device_pixel_ratio double precision,
    user_agent character varying(500),
    connection_type character varying(50),
    connection_speed double precision,
    model_name character varying(100),
    firmware_version character varying(50),
    status character varying(20) NOT NULL,
    last_seen_at timestamp with time zone,
    rotation integer DEFAULT 0 NOT NULL,
    is_volume_enabled boolean DEFAULT true NOT NULL,
    room_number character varying(50),
    location_type character varying(50) DEFAULT 'guest_room'::character varying NOT NULL,
    is_personalization_supported boolean DEFAULT true NOT NULL,
    privacy_mode character varying(20) DEFAULT 'limited'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    released_at timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    assigned_playlist_id integer,
    CONSTRAINT check_devices_screen_height_positive CHECK (((screen_height IS NULL) OR (screen_height > 0))),
    CONSTRAINT check_devices_screen_width_positive CHECK (((screen_width IS NULL) OR (screen_width > 0))),
    CONSTRAINT check_devices_viewport_height_positive CHECK (((viewport_height IS NULL) OR (viewport_height > 0))),
    CONSTRAINT check_devices_viewport_width_positive CHECK (((viewport_width IS NULL) OR (viewport_width > 0)))
);


ALTER TABLE public.devices OWNER TO signage_user;

--
-- Name: TABLE devices; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.devices IS 'Device registration and monitoring with multi-tenant support';


--
-- Name: COLUMN devices.device_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.device_type IS 'Device type: tv (WebOS/native app) or monitor (browser-based)';


--
-- Name: COLUMN devices.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.organization_id IS 'Organization ID - nullable for pending devices, assigned during activation';


--
-- Name: COLUMN devices.unique_code; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.unique_code IS '6-digit activation code (expires in 10 minutes)';


--
-- Name: COLUMN devices.device_uuid; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.device_uuid IS 'Unique device identifier for WebOS devices';


--
-- Name: COLUMN devices.status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.status IS 'Device status: pending (awaiting activation), active (operational), inactive (released)';


--
-- Name: COLUMN devices.last_seen_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.last_seen_at IS 'Timestamp when device last sent heartbeat or communication (renamed from last_seen)';


--
-- Name: COLUMN devices.rotation; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.rotation IS 'Screen rotation in degrees (0, 90, 180, 270) - DEFAULT: 0';


--
-- Name: COLUMN devices.is_volume_enabled; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.is_volume_enabled IS 'TRUE if device audio/volume is enabled, FALSE if muted/disabled';


--
-- Name: COLUMN devices.room_number; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.room_number IS 'Hotel room number (for hotel deployments)';


--
-- Name: COLUMN devices.location_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.location_type IS 'Device location type in hotel (guest_room, lobby, restaurant, etc.) - DEFAULT: guest_room';


--
-- Name: COLUMN devices.is_personalization_supported; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.is_personalization_supported IS 'TRUE if device supports PMS guest personalization features, FALSE otherwise';


--
-- Name: COLUMN devices.privacy_mode; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.privacy_mode IS 'Privacy level: none (full access), limited (restricted), full (maximum privacy) - DEFAULT: limited';


--
-- Name: COLUMN devices.released_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.released_at IS 'Timestamp when device was released (moved to inactive)';


--
-- Name: COLUMN devices.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.created_by_id IS 'User ID who created this device (FK to users.id)';


--
-- Name: COLUMN devices.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.updated_by_id IS 'User ID who last updated this device (FK to users.id)';


--
-- Name: CONSTRAINT check_devices_screen_height_positive ON devices; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_devices_screen_height_positive ON public.devices IS 'Ensures screen height is positive when specified';


--
-- Name: CONSTRAINT check_devices_screen_width_positive ON devices; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_devices_screen_width_positive ON public.devices IS 'Ensures screen width is positive when specified';


--
-- Name: CONSTRAINT check_devices_viewport_height_positive ON devices; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_devices_viewport_height_positive ON public.devices IS 'Ensures viewport height is positive when specified';


--
-- Name: CONSTRAINT check_devices_viewport_width_positive ON devices; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_devices_viewport_width_positive ON public.devices IS 'Ensures viewport width is positive when specified';


--
-- Name: device_engagement; Type: VIEW; Schema: public; Owner: signage_user
--

CREATE VIEW public.device_engagement AS
 SELECT d.id AS device_id,
    d.device_name,
    d.organization_id,
    count(*) AS total_plays,
    count(DISTINCT cpl.content_id) AS unique_content,
    max(cpl.started_at) AS last_playback_at,
    sum(cpl.duration_seconds) AS total_watch_time_seconds
   FROM (public.devices d
     LEFT JOIN public.content_playback_logs cpl ON ((cpl.device_id = d.id)))
  GROUP BY d.id, d.device_name, d.organization_id;


ALTER TABLE public.device_engagement OWNER TO signage_user;

--
-- Name: VIEW device_engagement; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON VIEW public.device_engagement IS 'Device engagement metrics for monitoring';


--
-- Name: device_group_members; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_group_members (
    id integer NOT NULL,
    device_id integer NOT NULL,
    group_id integer NOT NULL,
    joined_at timestamp with time zone DEFAULT now() NOT NULL,
    added_by_id integer
);


ALTER TABLE public.device_group_members OWNER TO signage_user;

--
-- Name: TABLE device_group_members; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_group_members IS 'Many-to-many: devices can belong to multiple groups';


--
-- Name: COLUMN device_group_members.added_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_group_members.added_by_id IS 'User ID who added this member (FK to users.id)';


--
-- Name: device_groups; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_groups (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description character varying(500),
    parent_group_id integer,
    organization_id integer NOT NULL,
    group_type character varying(50),
    sort_order integer DEFAULT 0,
    default_playlist_id integer,
    deleted_at timestamp with time zone,
    created_by_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.device_groups OWNER TO signage_user;

--
-- Name: TABLE device_groups; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_groups IS 'Hierarchical device groups for large-scale deployments';


--
-- Name: COLUMN device_groups.parent_group_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_groups.parent_group_id IS 'Self-referencing: allows unlimited depth hierarchy';


--
-- Name: COLUMN device_groups.group_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_groups.group_type IS 'Suggested types: chain, hotel, floor, location, custom';


--
-- Name: COLUMN device_groups.default_playlist_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_groups.default_playlist_id IS 'Playlist inherited by child groups (if NULL, check parent)';


--
-- Name: COLUMN device_groups.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_groups.created_by_id IS 'User ID who created this group (FK to users.id)';


--
-- Name: device_group_hierarchy; Type: VIEW; Schema: public; Owner: signage_user
--

CREATE VIEW public.device_group_hierarchy AS
 SELECT dg.id,
    dg.name,
    dg.group_type,
    dg.parent_group_id,
    pg.name AS parent_name,
    public.get_group_path(dg.id) AS full_path,
    count(dgm.device_id) AS direct_devices
   FROM ((public.device_groups dg
     LEFT JOIN public.device_groups pg ON ((pg.id = dg.parent_group_id)))
     LEFT JOIN public.device_group_members dgm ON ((dgm.group_id = dg.id)))
  WHERE (dg.deleted_at IS NULL)
  GROUP BY dg.id, dg.name, dg.group_type, dg.parent_group_id, pg.name;


ALTER TABLE public.device_group_hierarchy OWNER TO signage_user;

--
-- Name: VIEW device_group_hierarchy; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON VIEW public.device_group_hierarchy IS 'Hierarchical view of all device groups with breadcrumb paths';


--
-- Name: device_group_members_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_group_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_group_members_id_seq OWNER TO signage_user;

--
-- Name: device_group_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_group_members_id_seq OWNED BY public.device_group_members.id;


--
-- Name: device_group_stats; Type: VIEW; Schema: public; Owner: signage_user
--

CREATE VIEW public.device_group_stats AS
 SELECT dg.id AS group_id,
    dg.name AS group_name,
    dg.organization_id,
    count(DISTINCT dgm.device_id) AS total_devices,
    count(DISTINCT dgm.device_id) FILTER (WHERE ((d.status)::text = 'online'::text)) AS online_devices,
    count(DISTINCT dgm.device_id) FILTER (WHERE ((d.status)::text = 'offline'::text)) AS offline_devices
   FROM ((public.device_groups dg
     LEFT JOIN public.device_group_members dgm ON ((dgm.group_id = dg.id)))
     LEFT JOIN public.devices d ON ((d.id = dgm.device_id)))
  WHERE (dg.deleted_at IS NULL)
  GROUP BY dg.id, dg.name, dg.organization_id;


ALTER TABLE public.device_group_stats OWNER TO signage_user;

--
-- Name: VIEW device_group_stats; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON VIEW public.device_group_stats IS 'Device count and status per group';


--
-- Name: device_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_groups_id_seq OWNER TO signage_user;

--
-- Name: device_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_groups_id_seq OWNED BY public.device_groups.id;


--
-- Name: device_health_metrics; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_health_metrics (
    id integer NOT NULL,
    device_id integer NOT NULL,
    organization_id integer NOT NULL,
    cpu_usage numeric(5,2),
    memory_usage numeric(5,2),
    disk_usage numeric(5,2),
    temperature numeric(5,2),
    network_status character varying(20),
    bandwidth_up integer,
    bandwidth_down integer,
    latency integer,
    display_status character varying(20),
    resolution character varying(20),
    refresh_rate integer,
    browser_version character varying(100),
    user_agent text,
    recorded_at timestamp without time zone DEFAULT now(),
    memory_total_mb integer,
    memory_used_mb integer,
    disk_total_gb integer,
    disk_used_gb integer,
    network_latency_ms integer,
    network_download_mbps numeric(10,2),
    network_upload_mbps numeric(10,2),
    connection_quality character varying(20),
    display_resolution character varying(20),
    display_refresh_rate integer,
    gpu_usage numeric(5,2),
    player_version character varying(50),
    player_uptime_hours integer,
    content_errors_count integer DEFAULT 0,
    last_error_message text,
    last_error_at timestamp with time zone,
    overall_status character varying(20) DEFAULT 'healthy'::character varying,
    is_alert_triggered boolean DEFAULT false,
    alert_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.device_health_metrics OWNER TO signage_user;

--
-- Name: COLUMN device_health_metrics.is_alert_triggered; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_health_metrics.is_alert_triggered IS 'TRUE if health metric triggered an alert condition, FALSE if healthy';


--
-- Name: device_health_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_health_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_health_metrics_id_seq OWNER TO signage_user;

--
-- Name: device_health_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_health_metrics_id_seq OWNED BY public.device_health_metrics.id;


--
-- Name: device_logs; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_logs (
    id integer NOT NULL,
    device_id integer NOT NULL,
    organization_id integer NOT NULL,
    log_level character varying(20) NOT NULL,
    message text NOT NULL,
    source character varying(500),
    stack_trace text,
    user_agent character varying(500),
    url character varying(1000),
    recorded_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT device_logs_log_level_check CHECK (((log_level)::text = ANY ((ARRAY['log'::character varying, 'info'::character varying, 'warn'::character varying, 'error'::character varying, 'debug'::character varying])::text[])))
);


ALTER TABLE public.device_logs OWNER TO signage_user;

--
-- Name: TABLE device_logs; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_logs IS 'Remote console logs from devices for debugging';


--
-- Name: COLUMN device_logs.log_level; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_logs.log_level IS 'Log severity: log (general), info, warn, error, debug';


--
-- Name: COLUMN device_logs.source; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_logs.source IS 'Code location where log originated (file:line)';


--
-- Name: COLUMN device_logs.stack_trace; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_logs.stack_trace IS 'Error stack trace for debugging';


--
-- Name: COLUMN device_logs.recorded_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_logs.recorded_at IS 'Timestamp when log entry was recorded (renamed from timestamp)';


--
-- Name: device_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_logs_id_seq OWNER TO signage_user;

--
-- Name: device_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_logs_id_seq OWNED BY public.device_logs.id;


--
-- Name: device_speed_tests; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_speed_tests (
    id integer NOT NULL,
    device_id integer NOT NULL,
    organization_id integer NOT NULL,
    download_speed numeric(10,2),
    upload_speed numeric(10,2),
    latency integer,
    jitter integer,
    packet_loss numeric(5,2),
    dns_server character varying(45),
    server_endpoint character varying(255),
    quality character varying(20),
    test_duration_ms integer,
    error_message text,
    tested_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT device_speed_tests_quality_check CHECK (((quality)::text = ANY ((ARRAY['good'::character varying, 'fair'::character varying, 'poor'::character varying])::text[])))
);


ALTER TABLE public.device_speed_tests OWNER TO signage_user;

--
-- Name: TABLE device_speed_tests; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_speed_tests IS 'Network speed test results history';


--
-- Name: COLUMN device_speed_tests.download_speed; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_speed_tests.download_speed IS 'Download speed in Mbps';


--
-- Name: COLUMN device_speed_tests.upload_speed; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_speed_tests.upload_speed IS 'Upload speed in Mbps';


--
-- Name: COLUMN device_speed_tests.latency; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_speed_tests.latency IS 'Network latency (ping) in milliseconds';


--
-- Name: COLUMN device_speed_tests.quality; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_speed_tests.quality IS 'Test result quality: good (>=25 Mbps down), fair (>=10 Mbps), poor (<10 Mbps)';


--
-- Name: device_speed_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_speed_tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_speed_tests_id_seq OWNER TO signage_user;

--
-- Name: device_speed_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_speed_tests_id_seq OWNED BY public.device_speed_tests.id;


--
-- Name: device_tags; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.device_tags (
    id integer NOT NULL,
    device_id integer NOT NULL,
    tag_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    assigned_by_id integer
);


ALTER TABLE public.device_tags OWNER TO signage_user;

--
-- Name: TABLE device_tags; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_tags IS 'Many-to-many relationship between devices and tags for organization and content routing';


--
-- Name: COLUMN device_tags.device_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_tags.device_id IS 'Reference to device';


--
-- Name: COLUMN device_tags.tag_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_tags.tag_id IS 'Reference to tag';


--
-- Name: COLUMN device_tags.assigned_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_tags.assigned_at IS 'Timestamp when tag was assigned to device';


--
-- Name: COLUMN device_tags.assigned_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_tags.assigned_by_id IS 'User ID who assigned this tag (FK to users.id)';


--
-- Name: device_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.device_tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.device_tags_id_seq OWNER TO signage_user;

--
-- Name: device_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.device_tags_id_seq OWNED BY public.device_tags.id;


--
-- Name: devices_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.devices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.devices_id_seq OWNER TO signage_user;

--
-- Name: devices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.devices_id_seq OWNED BY public.devices.id;


--
-- Name: mv_organization_health_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: signage_user
--

CREATE MATERIALIZED VIEW public.mv_organization_health_summary AS
 SELECT d.organization_id,
    count(DISTINCT d.id) AS total_devices,
    count(DISTINCT
        CASE
            WHEN ((dhm.network_status)::text = 'online'::text) THEN d.id
            ELSE NULL::integer
        END) AS online_devices,
    count(DISTINCT
        CASE
            WHEN (dhm.cpu_usage > (80)::numeric) THEN d.id
            ELSE NULL::integer
        END) AS high_cpu_devices,
    count(DISTINCT
        CASE
            WHEN (dhm.memory_usage > (80)::numeric) THEN d.id
            ELSE NULL::integer
        END) AS high_memory_devices,
    count(DISTINCT
        CASE
            WHEN (dhm.temperature > (75)::numeric) THEN d.id
            ELSE NULL::integer
        END) AS high_temp_devices,
    round(avg(dhm.cpu_usage), 2) AS avg_cpu_usage,
    round(avg(dhm.memory_usage), 2) AS avg_memory_usage,
    round(avg(dhm.latency), 2) AS avg_latency,
    max(dhm.recorded_at) AS last_updated
   FROM (public.devices d
     LEFT JOIN LATERAL ( SELECT device_health_metrics.id,
            device_health_metrics.device_id,
            device_health_metrics.organization_id,
            device_health_metrics.cpu_usage,
            device_health_metrics.memory_usage,
            device_health_metrics.disk_usage,
            device_health_metrics.temperature,
            device_health_metrics.network_status,
            device_health_metrics.bandwidth_up,
            device_health_metrics.bandwidth_down,
            device_health_metrics.latency,
            device_health_metrics.display_status,
            device_health_metrics.resolution,
            device_health_metrics.refresh_rate,
            device_health_metrics.browser_version,
            device_health_metrics.user_agent,
            device_health_metrics.recorded_at
           FROM public.device_health_metrics
          WHERE (device_health_metrics.device_id = d.id)
          ORDER BY device_health_metrics.recorded_at DESC
         LIMIT 1) dhm ON (true))
  GROUP BY d.organization_id
  WITH NO DATA;


ALTER TABLE public.mv_organization_health_summary OWNER TO signage_user;

--
-- Name: organizations; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.organizations (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    pin character varying(8),
    description character varying(500),
    address character varying(500),
    contact_email character varying(100),
    contact_phone character varying(20),
    logo_url character varying(500),
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    max_devices integer DEFAULT 10 NOT NULL,
    max_users integer DEFAULT 5 NOT NULL,
    settings jsonb DEFAULT '{}'::jsonb,
    CONSTRAINT check_organizations_max_devices_positive CHECK ((max_devices > 0)),
    CONSTRAINT check_organizations_max_users_positive CHECK ((max_users > 0))
);


ALTER TABLE public.organizations OWNER TO signage_user;

--
-- Name: COLUMN organizations.pin; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.organizations.pin IS 'Organization PIN/code for access control (optional)';


--
-- Name: CONSTRAINT check_organizations_max_devices_positive ON organizations; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_organizations_max_devices_positive ON public.organizations IS 'Ensures organization can have at least 1 device (business rule)';


--
-- Name: CONSTRAINT check_organizations_max_users_positive ON organizations; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_organizations_max_users_positive ON public.organizations IS 'Ensures organization can have at least 1 user (business rule)';


--
-- Name: organizations_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.organizations_id_seq OWNER TO signage_user;

--
-- Name: organizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.organizations_id_seq OWNED BY public.organizations.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token_hash character varying(64) NOT NULL,
    email character varying(100) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    consumed_at timestamp with time zone
);


ALTER TABLE public.password_reset_tokens OWNER TO signage_user;

--
-- Name: TABLE password_reset_tokens; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.password_reset_tokens IS 'Database-backed password reset tokens (Fix P0-7)';


--
-- Name: COLUMN password_reset_tokens.token_hash; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.password_reset_tokens.token_hash IS 'SHA256 hash of reset token';


--
-- Name: COLUMN password_reset_tokens.consumed_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.password_reset_tokens.consumed_at IS 'Timestamp when token was used (prevents reuse)';


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

ALTER TABLE public.password_reset_tokens ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.password_reset_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: playlist_assignments; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.playlist_assignments (
    id integer NOT NULL,
    playlist_id integer NOT NULL,
    device_id integer,
    tag_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_assignment_type CHECK ((((device_id IS NOT NULL) AND (tag_id IS NULL)) OR ((device_id IS NULL) AND (tag_id IS NOT NULL))))
);


ALTER TABLE public.playlist_assignments OWNER TO signage_user;

--
-- Name: TABLE playlist_assignments; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.playlist_assignments IS 'Polymorphic assignments: playlist can be assigned to devices OR tags';


--
-- Name: CONSTRAINT check_assignment_type ON playlist_assignments; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_assignment_type ON public.playlist_assignments IS 'Ensures assignment is to device OR tag, not both';


--
-- Name: playlist_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.playlist_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.playlist_assignments_id_seq OWNER TO signage_user;

--
-- Name: playlist_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.playlist_assignments_id_seq OWNED BY public.playlist_assignments.id;


--
-- Name: playlist_contents; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.playlist_contents (
    id integer NOT NULL,
    playlist_id integer NOT NULL,
    content_id integer NOT NULL,
    order_index integer DEFAULT 0 NOT NULL,
    duration integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.playlist_contents OWNER TO signage_user;

--
-- Name: TABLE playlist_contents; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.playlist_contents IS 'Junction table: many-to-many relationship between playlists and contents';


--
-- Name: COLUMN playlist_contents.order_index; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlist_contents.order_index IS 'Display order in playlist (0-based)';


--
-- Name: COLUMN playlist_contents.duration; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlist_contents.duration IS 'Override content duration for this playlist (optional)';


--
-- Name: playlist_contents_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.playlist_contents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.playlist_contents_id_seq OWNER TO signage_user;

--
-- Name: playlist_contents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.playlist_contents_id_seq OWNED BY public.playlist_contents.id;


--
-- Name: playlist_widgets; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.playlist_widgets (
    id integer NOT NULL,
    playlist_id integer NOT NULL,
    widget_id integer NOT NULL,
    "position" integer DEFAULT 0,
    display_duration integer,
    z_index integer DEFAULT 100,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.playlist_widgets OWNER TO signage_user;

--
-- Name: playlist_widgets_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.playlist_widgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.playlist_widgets_id_seq OWNER TO signage_user;

--
-- Name: playlist_widgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.playlist_widgets_id_seq OWNED BY public.playlist_widgets.id;


--
-- Name: playlists; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.playlists (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    priority integer DEFAULT 0 NOT NULL,
    schedule jsonb,
    organization_id integer NOT NULL,
    created_by_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    is_default boolean DEFAULT false NOT NULL,
    is_pms_template boolean DEFAULT false NOT NULL,
    CONSTRAINT check_playlists_priority_non_negative CHECK ((priority >= 0))
);


ALTER TABLE public.playlists OWNER TO signage_user;

--
-- Name: TABLE playlists; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.playlists IS 'Playlists for organizing content playback with multi-tenant support';


--
-- Name: COLUMN playlists.priority; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlists.priority IS 'Playlist priority for conflict resolution (higher = more priority)';


--
-- Name: COLUMN playlists.schedule; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlists.schedule IS 'JSONB schedule configuration (days, time ranges, etc.)';


--
-- Name: COLUMN playlists.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlists.organization_id IS 'Multi-tenant: isolates playlists by organization';


--
-- Name: COLUMN playlists.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlists.created_by_id IS 'User ID who created this playlist (FK to users.id)';


--
-- Name: CONSTRAINT check_playlists_priority_non_negative ON playlists; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_playlists_priority_non_negative ON public.playlists IS 'Ensures priority is non-negative (higher priority = higher number)';


--
-- Name: playlists_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.playlists_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.playlists_id_seq OWNER TO signage_user;

--
-- Name: playlists_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.playlists_id_seq OWNED BY public.playlists.id;


--
-- Name: pms_configurations; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.pms_configurations (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    api_key character varying(255) NOT NULL,
    is_active boolean DEFAULT true,
    last_synced_at timestamp without time zone,
    sync_interval_minutes integer DEFAULT 5,
    created_by_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.pms_configurations OWNER TO signage_user;

--
-- Name: COLUMN pms_configurations.last_synced_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.pms_configurations.last_synced_at IS 'Timestamp of last successful sync with PMS system (renamed from last_sync)';


--
-- Name: COLUMN pms_configurations.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.pms_configurations.created_by_id IS 'User ID who created this config (FK to users.id)';


--
-- Name: pms_configurations_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.pms_configurations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pms_configurations_id_seq OWNER TO signage_user;

--
-- Name: pms_configurations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.pms_configurations_id_seq OWNED BY public.pms_configurations.id;


--
-- Name: pms_guests; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.pms_guests (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    guest_name character varying(255) NOT NULL,
    room_number character varying(50) NOT NULL,
    checkin_date timestamp without time zone NOT NULL,
    checkout_date timestamp without time zone NOT NULL,
    email character varying(255),
    phone character varying(50),
    country character varying(100),
    reservation_no character varying(100),
    synced_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    title character varying(50),
    balance numeric(10,2) DEFAULT 0,
    loyalty_level character varying(50),
    language character varying(10),
    special_requests text
);


ALTER TABLE public.pms_guests OWNER TO signage_user;

--
-- Name: COLUMN pms_guests.updated_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.pms_guests.updated_at IS 'Timestamp when guest record was last modified (renamed from last_updated)';


--
-- Name: pms_guests_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.pms_guests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pms_guests_id_seq OWNER TO signage_user;

--
-- Name: pms_guests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.pms_guests_id_seq OWNED BY public.pms_guests.id;


--
-- Name: pms_rooms; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.pms_rooms (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    room_number character varying(50) NOT NULL,
    room_type character varying(100),
    status character varying(50) NOT NULL,
    floor character varying(20),
    bed_type character varying(50),
    max_occupancy integer,
    synced_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.pms_rooms OWNER TO signage_user;

--
-- Name: pms_rooms_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.pms_rooms_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.pms_rooms_id_seq OWNER TO signage_user;

--
-- Name: pms_rooms_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.pms_rooms_id_seq OWNED BY public.pms_rooms.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    description character varying(200),
    organization_id integer,
    is_system_role boolean DEFAULT false NOT NULL,
    permissions jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    CONSTRAINT check_system_role_no_org CHECK ((((is_system_role = true) AND (organization_id IS NULL)) OR ((is_system_role = false) AND (organization_id IS NOT NULL)) OR ((is_system_role = false) AND (organization_id IS NULL))))
);


ALTER TABLE public.roles OWNER TO signage_user;

--
-- Name: TABLE roles; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.roles IS 'Role-Based Access Control (RBAC) system for multi-tenant permissions';


--
-- Name: COLUMN roles.name; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.name IS 'Role name (unique per organization, system roles have NULL organization_id)';


--
-- Name: COLUMN roles.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.organization_id IS 'NULL for system roles, organization ID for custom roles';


--
-- Name: COLUMN roles.is_system_role; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.is_system_role IS 'TRUE for built-in system roles (SUPER_ADMIN, ADMIN, VIEWER, etc.)';


--
-- Name: COLUMN roles.permissions; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.permissions IS 'JSONB permissions map: {"resource": ["action1", "action2"]}';


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO signage_user;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: schedules; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.schedules (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    playlist_id integer,
    start_date date NOT NULL,
    end_date date,
    start_time time without time zone,
    end_time time without time zone,
    recurrence_type character varying(20),
    recurrence_pattern jsonb,
    exceptions jsonb,
    priority integer DEFAULT 0,
    is_active boolean DEFAULT true,
    created_by_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    device_ids jsonb,
    tag_ids jsonb,
    applies_to_all boolean DEFAULT false,
    CONSTRAINT check_schedules_date_range CHECK (((end_date IS NULL) OR (end_date >= start_date))),
    CONSTRAINT check_schedules_priority_non_negative CHECK (((priority IS NULL) OR (priority >= 0))),
    CONSTRAINT check_schedules_time_range CHECK (((end_time IS NULL) OR (start_time IS NULL) OR (end_date IS NOT NULL) OR (end_time > start_time)))
);


ALTER TABLE public.schedules OWNER TO signage_user;

--
-- Name: COLUMN schedules.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.schedules.created_by_id IS 'User ID who created this schedule (FK to users.id)';


--
-- Name: COLUMN schedules.applies_to_all; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.schedules.applies_to_all IS 'TRUE if schedule applies to all devices in organization, FALSE if assigned to specific devices/groups';


--
-- Name: CONSTRAINT check_schedules_date_range ON schedules; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_schedules_date_range ON public.schedules IS 'Ensures end date is on or after start date';


--
-- Name: CONSTRAINT check_schedules_priority_non_negative ON schedules; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_schedules_priority_non_negative ON public.schedules IS 'Ensures priority is non-negative (higher priority = higher number)';


--
-- Name: CONSTRAINT check_schedules_time_range ON schedules; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_schedules_time_range ON public.schedules IS 'Ensures end time is after start time for same-day schedules';


--
-- Name: schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.schedules_id_seq OWNER TO signage_user;

--
-- Name: schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.schedules_id_seq OWNED BY public.schedules.id;


--
-- Name: tags; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.tags (
    id integer NOT NULL,
    tag_name character varying(100) NOT NULL,
    description text,
    color character varying(7) NOT NULL,
    organization_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    priority integer DEFAULT 50 NOT NULL,
    assigned_playlist_id integer
);


ALTER TABLE public.tags OWNER TO signage_user;

--
-- Name: TABLE tags; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.tags IS 'Tags for organizing and categorizing content';


--
-- Name: COLUMN tags.color; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.tags.color IS 'Hex color code for tag display (e.g., #3B82F6)';


--
-- Name: COLUMN tags.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.tags.organization_id IS 'Organization ID for multi-tenant isolation';


--
-- Name: tags_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.tags_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tags_id_seq OWNER TO signage_user;

--
-- Name: tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.tags_id_seq OWNED BY public.tags.id;


--
-- Name: templates; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.templates (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    template_type character varying(50) NOT NULL,
    content text NOT NULL,
    variables jsonb,
    preview_data jsonb,
    is_active boolean DEFAULT true,
    created_by_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.templates OWNER TO signage_user;

--
-- Name: COLUMN templates.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.templates.created_by_id IS 'User ID who created this template (FK to users.id)';


--
-- Name: templates_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.templates_id_seq OWNER TO signage_user;

--
-- Name: templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.templates_id_seq OWNED BY public.templates.id;


--
-- Name: translations; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.translations (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_id integer NOT NULL,
    language_code character varying(5) NOT NULL,
    field_name character varying(100) NOT NULL,
    translated_value text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.translations OWNER TO signage_user;

--
-- Name: translations_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.translations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.translations_id_seq OWNER TO signage_user;

--
-- Name: translations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.translations_id_seq OWNED BY public.translations.id;


--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.user_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    organization_id integer,
    session_token character varying(64) NOT NULL,
    refresh_token character varying(64),
    ip_address character varying(45) NOT NULL,
    user_agent character varying(500),
    device_info jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_activity_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    session_type character varying(20) DEFAULT 'web'::character varying NOT NULL,
    CONSTRAINT check_refresh_token_expires CHECK (((refresh_token IS NULL) OR (expires_at > created_at))),
    CONSTRAINT user_sessions_session_type_check CHECK (((session_type)::text = ANY ((ARRAY['web'::character varying, 'api'::character varying, 'mobile'::character varying, 'device'::character varying])::text[])))
);


ALTER TABLE public.user_sessions OWNER TO signage_user;

--
-- Name: TABLE user_sessions; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.user_sessions IS 'Active user sessions for server-side JWT token management and security';


--
-- Name: COLUMN user_sessions.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.organization_id IS 'Organization ID (NULL for SUPER_ADMIN sessions)';


--
-- Name: COLUMN user_sessions.session_token; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.session_token IS 'SHA256 hash of JWT access token for verification';


--
-- Name: COLUMN user_sessions.refresh_token; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.refresh_token IS 'SHA256 hash of refresh token (optional)';


--
-- Name: COLUMN user_sessions.device_info; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.device_info IS 'JSONB: {"browser": "Chrome", "os": "Windows 10", "device": "Desktop"}';


--
-- Name: COLUMN user_sessions.last_activity_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.last_activity_at IS 'Timestamp of most recent user activity in this session (renamed from last_activity)';


--
-- Name: COLUMN user_sessions.revoked_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.revoked_at IS 'Manual logout timestamp (NULL = active)';


--
-- Name: COLUMN user_sessions.session_type; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.user_sessions.session_type IS 'Session type: web (browser), api (API client), mobile (app), device (TV)';


--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_sessions_id_seq OWNER TO signage_user;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.user_sessions_id_seq OWNED BY public.user_sessions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    full_name character varying(100) NOT NULL,
    organization_id integer,
    is_active boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    role_id integer
);


ALTER TABLE public.users OWNER TO signage_user;

--
-- Name: COLUMN users.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.users.organization_id IS 'Organization ID (NULL for SUPER_ADMIN system users)';


--
-- Name: COLUMN users.role_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.users.role_id IS 'User role (FK to roles.id) - SINGLE source of truth for user role';


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO signage_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: widgets; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.widgets (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    widget_type character varying(50) NOT NULL,
    config jsonb NOT NULL,
    layout jsonb,
    is_active boolean DEFAULT true,
    created_by_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.widgets OWNER TO signage_user;

--
-- Name: COLUMN widgets.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.widgets.created_by_id IS 'User ID who created this widget (FK to users.id)';


--
-- Name: widgets_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.widgets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.widgets_id_seq OWNER TO signage_user;

--
-- Name: widgets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.widgets_id_seq OWNED BY public.widgets.id;


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: content_assignments id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments ALTER COLUMN id SET DEFAULT nextval('public.content_assignments_id_seq'::regclass);


--
-- Name: content_playback_logs id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs ALTER COLUMN id SET DEFAULT nextval('public.content_playback_logs_id_seq'::regclass);


--
-- Name: content_tags id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags ALTER COLUMN id SET DEFAULT nextval('public.content_tags_id_seq'::regclass);


--
-- Name: contents id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents ALTER COLUMN id SET DEFAULT nextval('public.contents_id_seq'::regclass);


--
-- Name: device_commands id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_commands ALTER COLUMN id SET DEFAULT nextval('public.device_commands_id_seq'::regclass);


--
-- Name: device_group_members id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members ALTER COLUMN id SET DEFAULT nextval('public.device_group_members_id_seq'::regclass);


--
-- Name: device_groups id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups ALTER COLUMN id SET DEFAULT nextval('public.device_groups_id_seq'::regclass);


--
-- Name: device_health_metrics id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_health_metrics ALTER COLUMN id SET DEFAULT nextval('public.device_health_metrics_id_seq'::regclass);


--
-- Name: device_logs id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_logs ALTER COLUMN id SET DEFAULT nextval('public.device_logs_id_seq'::regclass);


--
-- Name: device_speed_tests id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_speed_tests ALTER COLUMN id SET DEFAULT nextval('public.device_speed_tests_id_seq'::regclass);


--
-- Name: device_tags id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags ALTER COLUMN id SET DEFAULT nextval('public.device_tags_id_seq'::regclass);


--
-- Name: devices id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices ALTER COLUMN id SET DEFAULT nextval('public.devices_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: playlist_assignments id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments ALTER COLUMN id SET DEFAULT nextval('public.playlist_assignments_id_seq'::regclass);


--
-- Name: playlist_contents id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_contents ALTER COLUMN id SET DEFAULT nextval('public.playlist_contents_id_seq'::regclass);


--
-- Name: playlist_widgets id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_widgets ALTER COLUMN id SET DEFAULT nextval('public.playlist_widgets_id_seq'::regclass);


--
-- Name: playlists id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists ALTER COLUMN id SET DEFAULT nextval('public.playlists_id_seq'::regclass);


--
-- Name: pms_configurations id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations ALTER COLUMN id SET DEFAULT nextval('public.pms_configurations_id_seq'::regclass);


--
-- Name: pms_guests id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_guests ALTER COLUMN id SET DEFAULT nextval('public.pms_guests_id_seq'::regclass);


--
-- Name: pms_rooms id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_rooms ALTER COLUMN id SET DEFAULT nextval('public.pms_rooms_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: schedules id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules ALTER COLUMN id SET DEFAULT nextval('public.schedules_id_seq'::regclass);


--
-- Name: tags id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags ALTER COLUMN id SET DEFAULT nextval('public.tags_id_seq'::regclass);


--
-- Name: templates id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates ALTER COLUMN id SET DEFAULT nextval('public.templates_id_seq'::regclass);


--
-- Name: translations id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations ALTER COLUMN id SET DEFAULT nextval('public.translations_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN id SET DEFAULT nextval('public.user_sessions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: widgets id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets ALTER COLUMN id SET DEFAULT nextval('public.widgets_id_seq'::regclass);


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.audit_logs (id, user_id, organization_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at) FROM stdin;
1	\N	\N	organization.create	organization	5	{"name": "TestAuditOrg", "pin": "12345678", "ip_address": "192.168.5.172"}	\N	\N	2025-11-05 13:38:35.746257+00
2	9	4	tag.create	tag	5	{"tag_name": "FinalAuditTest", "color": "#00D084"}	\N	\N	2025-11-06 01:03:03.714354+00
3	9	4	tag.update	tag	5	{"tag_name": "FinalAuditTestUpdated", "description": null, "color": "#FF6B6B"}	\N	\N	2025-11-06 01:03:04.838502+00
4	9	4	tag.delete	tag	1	{"force": false}	\N	\N	2025-11-06 01:03:58.478279+00
5	9	4	tag.create	tag	6	{"tag_name": "DeploymentTest", "color": "#3B82F6"}	\N	\N	2025-11-06 01:19:38.89296+00
6	9	\N	organization.delete	organization	3	{"ip_address": "192.168.5.172"}	\N	\N	2025-11-06 20:44:50.486433+00
7	9	\N	content.delete	content	2	{"title": "Test Image PNG", "content_type": "image", "file_url": "http://192.168.5.12:8001/content/images/2025/11/org_4/d04a9723-021d-4b62-a4c5-fcedc473731b.png", "organization_id": 4, "ip_address": "192.168.5.172"}	\N	\N	2025-11-06 20:56:18.163114+00
8	9	\N	content.delete	content	3	{"title": "Lounge Promo August", "content_type": "image", "file_url": "http://192.168.5.12:8001/content/images/2025/11/org_4/4c6ee543-627d-4db1-8ec9-21052161db52.jpg", "organization_id": 4, "ip_address": "192.168.5.172"}	\N	\N	2025-11-06 20:56:35.067079+00
9	9	4	tag.bulk_assign_contents	tag	6	{"content_count": 3, "assigned": 3, "skipped": 0, "failed": 0}	\N	\N	2025-11-07 01:21:02.056912+00
10	9	4	tag.bulk_assign_contents	tag	6	{"content_count": 3, "assigned": 0, "skipped": 3, "failed": 0}	\N	\N	2025-11-07 01:21:02.072479+00
11	9	4	tag.bulk_assign_contents	tag	6	{"content_count": 5, "assigned": 2, "skipped": 3, "failed": 0}	\N	\N	2025-11-07 01:21:02.093211+00
12	9	4	tag.bulk_assign_contents	tag	3	{"content_count": 2, "assigned": 2, "skipped": 0, "failed": 0}	\N	\N	2025-11-07 01:22:16.128073+00
13	9	\N	organization.create	organization	9	{"name": "DeepTest_Org_1763024487", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 09:01:29.867506+00
14	9	\N	organization.update	organization	9	{"name": "Updated_Org_1763024487", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 09:01:29.894204+00
15	9	\N	organization.create	organization	10	{"name": "Duplicate PIN Test", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 09:01:29.910238+00
16	9	\N	organization.create	organization	11	{"name": "TestOrg1_1763026309", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 09:31:50.347193+00
17	9	\N	organization.create	organization	12	{"name": "TestOrg2_1763026309", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 09:31:50.360581+00
18	9	4	tag.create	tag	7	{"tag_name": "TestTag_1763026577", "color": "#3B82F6"}	\N	\N	2025-11-13 09:36:17.71794+00
19	9	4	tag.create	tag	8	{"tag_name": "TestTag2_1763026577", "color": "#00FF00"}	\N	\N	2025-11-13 09:36:17.735585+00
20	9	4	tag.create	tag	9	{"tag_name": "TestTag_1763027068", "color": "#FF5733"}	\N	\N	2025-11-13 09:44:29.180423+00
21	9	\N	organization.create	organization	13	{"name": "TEST_ORG_CONTENT_TAG", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:20:26.741843+00
22	9	\N	organization.create	organization	14	{"name": "TEST_ORG_DEVICE_PLAYLIST", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:20:26.758615+00
23	9	\N	organization.create	organization	15	{"name": "TEST_ORG_SCHEDULE", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:20:26.772687+00
24	9	\N	organization.create	organization	16	{"name": "TEST_ORG_PMS_ANALYTICS", "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:20:26.785633+00
25	9	\N	user.create	user	14	{"username": "testadmin_ct", "email": "testadmin_ct@example.com", "role": "admin", "organization_id": 13, "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:25:31.566964+00
26	9	\N	user.create	user	15	{"username": "testadmin_dp", "email": "testadmin_dp@example.com", "role": "admin", "organization_id": 14, "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:25:32.002336+00
27	9	\N	user.create	user	16	{"username": "testadmin_sc", "email": "testadmin_sc@example.com", "role": "admin", "organization_id": 15, "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:25:32.425434+00
28	9	\N	user.create	user	17	{"username": "testadmin_pa", "email": "testadmin_pa@example.com", "role": "admin", "organization_id": 16, "ip_address": "192.168.5.172"}	\N	\N	2025-11-13 12:25:32.856128+00
29	9	\N	user.create	user	23	{"username": "bugfix_test_1763098428", "email": "bugfix_test_1763098428@test.com", "role": "viewer", "organization_id": 4, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 05:33:48.812842+00
30	9	\N	user.create	user	25	{"username": "p0_16_1763098922", "email": "p0_16_1763098922@test.com", "role": "viewer", "organization_id": 5, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 05:42:04.022511+00
31	9	\N	user.create	user	26	{"username": "p0_16_1763099705", "email": "p0_16_1763099705@test.com", "role": "viewer", "organization_id": 5, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 05:55:06.030168+00
32	26	\N	user.change_password	user	26	{"username": "p0_16_1763099705", "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 05:55:06.47234+00
33	9	\N	user.create	user	27	{"username": "p0_16_1763100011", "email": "p0_16_1763100011@test.com", "role": "viewer", "organization_id": 5, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:00:12.103369+00
34	27	\N	user.change_password	user	27	{"username": "p0_16_1763100011", "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:00:12.556082+00
35	9	\N	user.create	user	28	{"username": "p0_16_1763100128", "email": "p0_16_1763100128@test.com", "role": "viewer", "organization_id": 5, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:02:09.505878+00
36	28	\N	user.change_password	user	28	{"username": "p0_16_1763100128", "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:02:09.960133+00
37	9	\N	user.create	user	29	{"username": "p0_16_1763100763", "email": "p0_16_1763100763@test.com", "role": "viewer", "organization_id": 5, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:12:44.918396+00
38	29	\N	user.change_password	user	29	{"username": "p0_16_1763100763", "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 06:12:45.36611+00
39	9	\N	organization.create	organization	20	{"name": "Test Tenant Organization", "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 07:05:19.408054+00
40	9	\N	user.create	user	30	{"username": "tenant_admin", "email": "tenant_admin@test.com", "role": "admin", "organization_id": 20, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 07:05:19.641157+00
41	9	\N	user.create	user	31	{"username": "tenant_manager", "email": "tenant_manager@test.com", "role": "manager", "organization_id": 20, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 07:05:19.865811+00
42	9	\N	user.create	user	32	{"username": "tenant_viewer", "email": "tenant_viewer@test.com", "role": "viewer", "organization_id": 20, "ip_address": "192.168.5.172"}	\N	\N	2025-11-14 07:05:20.091473+00
\.


--
-- Data for Name: content_assignments; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.content_assignments (id, device_id, content_id, priority, schedule, assigned_at, assigned_by_id, expires_at, organization_id, tag_id, created_at, updated_at) FROM stdin;
8	7650	6	3	\N	2025-11-16 12:39:42.340484+00	\N	\N	4	\N	2025-11-16 12:39:42.340484+00	\N
9	7650	7	4	\N	2025-11-16 12:39:42.340484+00	\N	\N	4	\N	2025-11-16 12:39:42.340484+00	\N
10	7650	9	5	\N	2025-11-16 12:39:42.340484+00	\N	\N	4	\N	2025-11-16 12:39:42.340484+00	\N
12	7650	12	6	\N	2025-11-17 15:19:33.375945+00	\N	\N	4	\N	2025-11-17 15:19:33.375945+00	\N
\.


--
-- Data for Name: content_playback_logs; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.content_playback_logs (id, content_id, playlist_id, device_id, organization_id, started_at, ended_at, duration_seconds, is_completed, skip_reason, source, created_at) FROM stdin;
\.


--
-- Data for Name: content_tags; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.content_tags (id, content_id, tag_id, created_at) FROM stdin;
1	11	6	2025-11-07 01:21:02.05332+00
2	12	6	2025-11-07 01:21:02.053321+00
3	13	6	2025-11-07 01:21:02.053322+00
4	9	6	2025-11-07 01:21:02.091078+00
5	10	6	2025-11-07 01:21:02.091079+00
6	12	3	2025-11-07 01:22:16.122783+00
7	13	3	2025-11-07 01:22:16.122784+00
\.


--
-- Data for Name: contents; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.contents (id, title, description, content_type, file_path, file_url, storage_key, file_hash, duration, is_active, file_size, mime_type, original_filename, file_extension, resolution, width, height, codec, fps, bitrate, media_duration, video_start_time, video_end_time, audio_codec, audio_bitrate, audio_sample_rate, audio_channels, transcoding_status, transcoding_job_id, transcoding_progress, transcoding_error, hls_master_playlist_path, hls_master_playlist_url, hls_variants, thumbnail_path, thumbnail_url, thumbnail_generated_at, upload_status, organization_id, uploaded_by_id, created_at, updated_at, deleted_at) FROM stdin;
4	7a8108436af438ea86e989aa1b01bb00	\N	image	/data/signage/content/uploads/images/2025/11/org_4/a08ec884-0d25-4881-b51c-d7fde4011644.gif	http://192.168.5.12:8001/content/images/2025/11/org_4/a08ec884-0d25-4881-b51c-d7fde4011644.gif	images/2025/11/org_4/a08ec884-0d25-4881-b51c-d7fde4011644.gif	1035f560df8b4bd632b184a5feb080f584ac0010385c610a095ff0b6731fe2fa	10	f	240842	image/gif	7a8108436af438ea86e989aa1b01bb00.gif	.gif	500x382	500	382	gif	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	\N	\N	completed	4	9	2025-11-06 14:28:22.790862+00	2025-11-06 20:53:25.145961+00	2025-11-06 20:53:25.147917+00
2	Test Image PNG	Testing upload image	image	/data/signage/content/uploads/images/2025/11/org_4/d04a9723-021d-4b62-a4c5-fcedc473731b.png	http://192.168.5.12:8001/content/images/2025/11/org_4/d04a9723-021d-4b62-a4c5-fcedc473731b.png	images/2025/11/org_4/d04a9723-021d-4b62-a4c5-fcedc473731b.png	7ba193526c54f346e7594e7409100ad7d869c9396d00191d46794070c57a756a	15	f	1142207	image/png	Untitled design (8).png	.png	1886x827	1886	827	png	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	\N	\N	completed	4	9	2025-11-06 14:18:39.944126+00	2025-11-06 20:56:18.153252+00	2025-11-06 20:56:18.156076+00
3	Lounge Promo August	Promotional poster for lounge - August campaign	image	/data/signage/content/uploads/images/2025/11/org_4/4c6ee543-627d-4db1-8ec9-21052161db52.jpg	http://192.168.5.12:8001/content/images/2025/11/org_4/4c6ee543-627d-4db1-8ec9-21052161db52.jpg	images/2025/11/org_4/4c6ee543-627d-4db1-8ec9-21052161db52.jpg	d2b5671c5cb86f038583d9f7bc90a6e68509e50d28e7c6ea53e894989ca1afcd	20	f	3339217	image/jpeg	20250804 Lounge  promo agustus_Poster.jpg	.jpg	2756x3543	2756	3543	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	\N	\N	completed	4	9	2025-11-06 14:22:20.823638+00	2025-11-06 20:56:35.060171+00	2025-11-06 20:56:35.061538+00
7	pETANTANG	\N	image	/data/signage/content/uploads/images/2025/11/org_4/a313c2a7-c96f-40c1-8629-4e2b744a0e60.gif	http://192.168.5.12:8001/content/images/2025/11/org_4/a313c2a7-c96f-40c1-8629-4e2b744a0e60.gif	images/2025/11/org_4/a313c2a7-c96f-40c1-8629-4e2b744a0e60.gif	f5b05fc2f4fc51ff2546b7f8e949f4d641e02105a30b35141fda96b6ffa71ed4	10	t	7517252	image/gif	pETANTANG.gif	.gif	518x518	518	518	gif	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/a313c2a7-c96f-40c1-8629-4e2b744a0e60_thumb.jpg	\N	completed	4	9	2025-11-06 20:57:25.992985+00	2025-11-06 20:57:26.129948+00	\N
5	77b7a54bef9c9806c8f505aa02ad06c8	\N	video	/data/signage/content/uploads/videos/2025/11/org_4/438db452-3ee3-4bfa-8874-960e4d3dcf74.mp4	http://192.168.5.12:8001/content/videos/2025/11/org_4/438db452-3ee3-4bfa-8874-960e4d3dcf74.mp4	videos/2025/11/org_4/438db452-3ee3-4bfa-8874-960e4d3dcf74.mp4	b6f4fdec4b8437c63a3e2e8b74ddc4e0c4d24e4d1395163f0ae0b58ec03baec2	10	f	6007867	video/mp4	77b7a54bef9c9806c8f505aa02ad06c8.mp4	.mp4	\N	\N	\N	\N	\N	\N	\N	0	\N	\N	\N	\N	2	failed	\N	0	\N	\N	\N	\N	\N	\N	\N	completed	4	9	2025-11-06 14:28:34.331932+00	2025-11-06 20:53:18.197529+00	2025-11-06 20:53:18.199475+00
8	WhatsAppVideo2025-08-25at15.17.56-ezgif.com-crop	\N	image	/data/signage/content/uploads/images/2025/11/org_4/c3066c2d-77e0-4e16-bdd8-1918483affa3.gif	http://192.168.5.12:8001/content/images/2025/11/org_4/c3066c2d-77e0-4e16-bdd8-1918483affa3.gif	images/2025/11/org_4/c3066c2d-77e0-4e16-bdd8-1918483affa3.gif	e49f58791400c01647fa74207830793520201e06af63b687ee4aaddf07c34e28	10	t	14380115	image/gif	WhatsAppVideo2025-08-25at15.17.56-ezgif.com-crop.gif	.gif	478x850	478	850	gif	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/c3066c2d-77e0-4e16-bdd8-1918483affa3_thumb.jpg	\N	completed	4	9	2025-11-06 21:04:04.573333+00	2025-11-06 21:04:04.712316+00	\N
9	WhatsApp Image 2024-11-05 at 18.20.08	\N	image	/data/signage/content/uploads/images/2025/11/org_4/35ed4d4b-6ba2-4e58-89e7-17b419bf93d4.jpeg	http://192.168.5.12:8001/content/images/2025/11/org_4/35ed4d4b-6ba2-4e58-89e7-17b419bf93d4.jpeg	images/2025/11/org_4/35ed4d4b-6ba2-4e58-89e7-17b419bf93d4.jpeg	21f24597e4e07c3abbacbab0aa93946628a211e28da17fc9ede8d2be93e29bb9	10	t	283049	image/jpeg	WhatsApp Image 2024-11-05 at 18.20.08.jpeg	.jpeg	1539x597	1539	597	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/35ed4d4b-6ba2-4e58-89e7-17b419bf93d4_thumb.jpg	\N	completed	4	9	2025-11-06 21:04:04.588396+00	2025-11-06 21:04:04.729173+00	\N
10	WhatsApp Image 2024-11-26 at 08.37.07	\N	image	/data/signage/content/uploads/images/2025/11/org_4/8cf09269-e286-4607-a711-b28460fd668f.jpeg	http://192.168.5.12:8001/content/images/2025/11/org_4/8cf09269-e286-4607-a711-b28460fd668f.jpeg	images/2025/11/org_4/8cf09269-e286-4607-a711-b28460fd668f.jpeg	c004a7c85e5a0bd87214b40cc52b0614b41795bd929d1eb9b9d34029b6596942	10	t	176266	image/jpeg	WhatsApp Image 2024-11-26 at 08.37.07.jpeg	.jpeg	1600x1200	1600	1200	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/8cf09269-e286-4607-a711-b28460fd668f_thumb.jpg	\N	completed	4	9	2025-11-06 21:04:04.724566+00	2025-11-06 21:04:04.735911+00	\N
11	frwf	\N	image	/data/signage/content/uploads/images/2025/11/org_4/365f134c-0379-48d8-a842-997a3b67be83.jpg	http://192.168.5.12:8001/content/images/2025/11/org_4/365f134c-0379-48d8-a842-997a3b67be83.jpg	images/2025/11/org_4/365f134c-0379-48d8-a842-997a3b67be83.jpg	8f6ecaf006d8b7a1545c3e8def38f55ddb848ce2cc941a192cbe2595303fd373	10	t	167147	image/jpeg	frwf.jpg	.jpg	1886x827	1886	827	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/365f134c-0379-48d8-a842-997a3b67be83_thumb.jpg	\N	completed	4	9	2025-11-06 21:04:04.732924+00	2025-11-06 21:04:04.760932+00	\N
13	greeting_jepang	\N	audio	/data/signage/content/uploads/audios/2025/11/org_4/dad35b91-5557-4a50-bf5f-cf8326131b48.mp3	http://192.168.5.12:8001/content/audios/2025/11/org_4/dad35b91-5557-4a50-bf5f-cf8326131b48.mp3	audios/2025/11/org_4/dad35b91-5557-4a50-bf5f-cf8326131b48.mp3	080ce9b870222f072a4da51b3c300dc10f0c337164905d6ab63c2dfd96ab2666	3	t	28416	audio/mpeg	greeting_jepang.mp3	.mp3	\N	\N	\N	\N	\N	64	3.552	0	\N	mp3	64	24000	1	pending	\N	0	\N	\N	\N	\N	\N	\N	\N	completed	4	9	2025-11-06 21:07:03.956233+00	\N	\N
12	WhatsApp Video 2025-07-21 at 16.16.06 (1)	\N	video	/data/signage/content/uploads/videos/2025/11/org_4/e804e41a-b36a-4fcf-bbf3-781f164ec221.mp4	http://192.168.5.12:8001/content/videos/2025/11/org_4/e804e41a-b36a-4fcf-bbf3-781f164ec221.mp4	videos/2025/11/org_4/e804e41a-b36a-4fcf-bbf3-781f164ec221.mp4	a17a42c603d343b09ca515a963c072551f55b1632360d2cb72167bdbd80cea6b	40	t	1967872	video/mp4	WhatsApp Video 2025-07-21 at 16.16.06 (1).mp4	.mp4	640x360	640	360	h264	30	262	40	0	\N	\N	\N	\N	2	completed	\N	100	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/e804e41a-b36a-4fcf-bbf3-781f164ec221_thumb.jpg	\N	completed	4	9	2025-11-06 21:04:04.738694+00	2025-11-06 21:04:06.979375+00	\N
14	WhatsApp Image 2024-10-30 at 09.36.40	\N	image	/data/signage/content/uploads/images/2025/11/org_4/987e1c0b-eec2-41e0-90be-385cb146821a.jpeg	http://192.168.5.12:8001/content/images/2025/11/org_4/987e1c0b-eec2-41e0-90be-385cb146821a.jpeg	images/2025/11/org_4/987e1c0b-eec2-41e0-90be-385cb146821a.jpeg	94c76e8175462621e212cfd6f1bb6a6abec6c827e403dae2382862cefa8e46bb	10	t	107372	image/jpeg	WhatsApp Image 2024-10-30 at 09.36.40.jpeg	.jpeg	1080x968	1080	968	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/987e1c0b-eec2-41e0-90be-385cb146821a_thumb.jpg	\N	completed	4	9	2025-11-07 04:26:43.512233+00	2025-11-07 04:26:43.61189+00	\N
15	Screenshot_2	\N	image	/data/signage/content/uploads/images/2025/11/org_4/cfed3b02-b467-400f-ae70-70771a078a89.png	http://192.168.5.12:8001/content/images/2025/11/org_4/cfed3b02-b467-400f-ae70-70771a078a89.png	images/2025/11/org_4/cfed3b02-b467-400f-ae70-70771a078a89.png	58d2df01abe052b142e8ba34eb65fad1bdb36943493aea2aed3ebb419c680e4a	10	t	35181	image/png	Screenshot_2.png	.png	427x620	427	620	png	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/cfed3b02-b467-400f-ae70-70771a078a89_thumb.jpg	\N	completed	4	9	2025-11-11 02:06:31.208397+00	2025-11-11 02:06:31.41875+00	\N
16	Test_Upload_1763029283	Real JPG file upload test	image	/data/signage/content/uploads/4/image/2025/11/5f775876-55ed-4765-bada-fc274b86afaf_3f6f8eb1.jpg	http://192.168.5.12:8001/content/images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg	images/2025/11/org_4/5f775876-55ed-4765-bada-fc274b86afaf.jpg	21530a16ba0c49d91e2fdcf1c09347df32507c034513c3406aab23d2659a0083	10	t	254157	image/jpeg	test_image.jpg	.jpg	1886x827	1886	827	jpeg	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/5f775876-55ed-4765-bada-fc274b86afaf_3f6f8eb1_thumb.jpg	\N	completed	4	9	2025-11-13 10:21:24.273178+00	2025-11-13 10:21:24.402169+00	\N
17	Test Image	\N	image	/data/signage/content/uploads/4/image/2025/11/c6373975-0626-45ee-b1d4-628da6d5f4e6_726b12eb.png	http://192.168.5.12:8001/content/images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png	images/2025/11/org_4/c6373975-0626-45ee-b1d4-628da6d5f4e6.png	b09d17d9307d00d08616ba83b9bdb5b6c5a4f430f3dcf7053e3cb76b39089a6e	10	t	22835	image/png	bfdbfdbfd.PNG	.png	303x125	303	125	png	\N	\N	\N	0	\N	\N	\N	\N	2	pending	\N	0	\N	\N	\N	\N	\N	http://192.168.5.12:8001/thumbnails/c6373975-0626-45ee-b1d4-628da6d5f4e6_726b12eb_thumb.jpg	\N	completed	4	9	2025-11-13 12:31:58.670531+00	2025-11-13 12:31:58.841408+00	\N
6	Serangkaian Program menuju _13ravely to be Different_ GZJBBK	\N	video	/data/signage/content/uploads/videos/2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6.mp4	http://192.168.5.12:8001/content/videos/2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6.mp4	videos/2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6.mp4	d571be967147c2af6de26bc13b3eef6534ad1ff5f7731f0eeb8e61f89d8c22d7	59	t	4842296	video/mp4	Serangkaian Program menuju _13ravely to be Different_ GZJBBK.mp4	.mp4	636x360	636	360	h264	30	517	59.721723	0	\N	\N	\N	\N	2	completed	576d8ba9-e708-4930-abad-81a39aae6cdf	100	\N	2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6_hls/master.m3u8	http://192.168.5.12:8001/content/hls/2025/11/org_4/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6/master.m3u8	"{\\"qualities\\": [\\"360p\\"]}"	\N	http://192.168.5.12:8001/thumbnails/e9dff2be-eb88-41c8-b5aa-a47b9e957fd6_thumb.jpg	\N	completed	4	9	2025-11-06 20:37:02.437262+00	2025-11-17 17:19:21.586916+00	\N
\.


--
-- Data for Name: device_commands; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_commands (id, device_id, organization_id, command_type, parameters, reason, status, sent_at, executed_at, error_message, created_by_id, expires_at, created_at, command_data, priority, failed_at, result, retry_count, max_retries, updated_at) FROM stdin;
\.


--
-- Data for Name: device_connection_logs; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_connection_logs (id, device_id, logged_at, event_type, status, latency_ms, error_message, download_speed_mbps, upload_speed_mbps, metadata, created_at, connection_type, effective_type, rtt_ms, endpoint, http_status, test_trigger, test_duration_ms) FROM stdin;
1	6178	2025-11-15 15:43:44.068+00	network	online	45	\N	\N	\N	{"test": true}	2025-11-15 15:43:44.131476+00	\N	\N	\N	\N	\N	\N	\N
2	6178	2025-11-15 15:43:14.069+00	server	connected	120	\N	\N	\N	{"endpoint": "/api/v1/devices/heartbeat"}	2025-11-15 15:43:44.131476+00	\N	\N	\N	\N	\N	\N	\N
3	6178	2025-11-15 15:42:44.069+00	speed_test	tested	35	\N	98.50	45.20	{"test_duration_ms": 5000}	2025-11-15 15:43:44.131476+00	\N	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: device_group_members; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_group_members (id, device_id, group_id, joined_at, added_by_id) FROM stdin;
\.


--
-- Data for Name: device_groups; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_groups (id, name, description, parent_group_id, organization_id, group_type, sort_order, default_playlist_id, deleted_at, created_by_id, created_at, updated_at) FROM stdin;
1	test	\N	\N	4	location	0	\N	\N	9	2025-11-11 02:15:04.948374+00	\N
2	Test Group - Lobby Displays	All displays in hotel lobbies	\N	20	location	0	\N	\N	30	2025-11-14 07:11:24.593027+00	\N
4	Floor 1 Lobby	First floor lobby displays	3	20	floor	0	\N	\N	30	2025-11-14 07:12:20.288972+00	\N
3	Test Group - Lobby Displays (Updated)	Updated description	\N	20	location	0	\N	\N	30	2025-11-14 07:12:20.265086+00	2025-11-14 07:12:20.328238+00
\.


--
-- Data for Name: device_health_metrics; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_health_metrics (id, device_id, organization_id, cpu_usage, memory_usage, disk_usage, temperature, network_status, bandwidth_up, bandwidth_down, latency, display_status, resolution, refresh_rate, browser_version, user_agent, recorded_at, memory_total_mb, memory_used_mb, disk_total_gb, disk_used_gb, network_latency_ms, network_download_mbps, network_upload_mbps, connection_quality, display_resolution, display_refresh_rate, gpu_usage, player_version, player_uptime_hours, content_errors_count, last_error_message, last_error_at, overall_status, is_alert_triggered, alert_message, metadata, created_at) FROM stdin;
\.


--
-- Data for Name: device_logs; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_logs (id, device_id, organization_id, log_level, message, source, stack_trace, user_agent, url, recorded_at) FROM stdin;
\.


--
-- Data for Name: device_speed_tests; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_speed_tests (id, device_id, organization_id, download_speed, upload_speed, latency, jitter, packet_loss, dns_server, server_endpoint, quality, test_duration_ms, error_message, tested_at) FROM stdin;
\.


--
-- Data for Name: device_tags; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.device_tags (id, device_id, tag_id, assigned_at, assigned_by_id) FROM stdin;
\.


--
-- Data for Name: devices; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.devices (id, device_type, device_name, organization_id, unique_code, code_expires_at, device_uuid, ip_address, platform, screen_width, screen_height, viewport_width, viewport_height, device_pixel_ratio, user_agent, connection_type, connection_speed, model_name, firmware_version, status, last_seen_at, rotation, is_volume_enabled, room_number, location_type, is_personalization_supported, privacy_mode, created_at, updated_at, released_at, created_by_id, updated_by_id, assigned_playlist_id) FROM stdin;
6182	monitor	DeviceX_Schedule	15	291702	2025-11-13 12:50:16.43865+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:40:16.448773+00	0	t	\N	guest_room	t	limited	2025-11-13 12:40:16.438183+00	2025-11-13 12:40:16.448206+00	\N	\N	\N	23
6178	monitor	New Device	\N	123456	2025-11-13 12:35:59.054039+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-13 12:25:59.053231+00	\N	\N	\N	\N	\N
6179	monitor	New Device	\N	134690	2025-11-13 12:41:37.440187+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-13 12:31:37.439468+00	\N	\N	\N	\N	\N
6183	monitor	DeviceY_Schedule	15	694305	2025-11-13 12:50:16.462301+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:40:16.471288+00	0	t	\N	guest_room	t	limited	2025-11-13 12:40:16.461815+00	2025-11-13 12:40:16.470825+00	\N	\N	\N	\N
6184	monitor	DeviceX_Schedule	15	969621	2025-11-13 12:52:01.339621+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:42:01.348918+00	0	t	\N	guest_room	t	limited	2025-11-13 12:42:01.339191+00	2025-11-13 12:42:01.348428+00	\N	\N	\N	\N
6185	monitor	DeviceY_Schedule	15	104136	2025-11-13 12:52:01.35904+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:42:01.368951+00	0	t	\N	guest_room	t	limited	2025-11-13 12:42:01.358487+00	2025-11-13 12:42:01.368438+00	\N	\N	\N	\N
6186	monitor	DeviceX_Schedule	15	462463	2025-11-13 12:53:14.570559+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:43:14.580045+00	0	t	\N	guest_room	t	limited	2025-11-13 12:43:14.570092+00	2025-11-13 12:43:14.579546+00	\N	\N	\N	\N
6187	monitor	DeviceY_Schedule	15	461021	2025-11-13 12:53:14.590529+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-13 12:43:14.599442+00	0	t	\N	guest_room	t	limited	2025-11-13 12:43:14.58992+00	2025-11-13 12:43:14.598995+00	\N	\N	\N	\N
6188	monitor	Test Device 1763049170	\N	349956	2025-11-13 16:02:53.110828+00	\N	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-13 15:52:53.108375+00	\N	\N	\N	\N	\N
6190	monitor	Expiry Test 263711	\N	263711	2025-11-14 03:33:04.759172+00	a2dc0997-bd37-4b4c-8470-1977e1cd8ce8	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:23:04.758703+00	\N	\N	\N	\N	\N
6191	monitor	Retry Test 0	\N	254702	2025-11-14 03:33:04.786203+00	aa272680-6793-419e-8195-01321f7e4a3f	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:23:04.785621+00	\N	\N	\N	\N	\N
6192	monitor	Retry Test 1	\N	091096	2025-11-14 03:33:04.794774+00	d318d74e-cf4e-45a2-82dd-12975849288d	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:23:04.794347+00	\N	\N	\N	\N	\N
6193	monitor	Retry Test 2	\N	858548	2025-11-14 03:33:04.80301+00	5fd26413-0a56-477a-8565-41c80e3feb69	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:23:04.802549+00	\N	\N	\N	\N	\N
6195	monitor	Expiry Test 881161	\N	881161	2025-11-14 03:34:57.420716+00	b442dccf-0354-4266-b170-b3c4189865e0	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:24:57.42004+00	\N	\N	\N	\N	\N
6196	monitor	Retry Test 0	\N	482756	2025-11-14 03:34:57.459229+00	6a1d5be1-7c1b-402f-8b20-2fab1e200396	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:24:57.458709+00	\N	\N	\N	\N	\N
6197	monitor	Retry Test 1	\N	337143	2025-11-14 03:34:58.467835+00	b9276b55-05ec-434b-8883-9b33f7aa9bf9	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:24:58.46724+00	\N	\N	\N	\N	\N
6198	monitor	Retry Test 2	\N	448576	2025-11-14 03:34:58.480396+00	ff8b81df-6530-45c9-bfc9-933b6a85c410	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:24:58.479905+00	\N	\N	\N	\N	\N
6201	monitor	Expiry Test 229970	\N	229970	2025-11-14 03:37:25.171645+00	6bebbcf7-f7bd-463a-95b2-51698b65342c	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:25.171125+00	\N	\N	\N	\N	\N
6202	monitor	Retry Test 0	\N	583136	2025-11-14 03:37:25.209846+00	0eeb876d-42a4-4c08-a03a-d0a9953c479a	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:25.209206+00	\N	\N	\N	\N	\N
6203	monitor	Retry Test 1	\N	284323	2025-11-14 03:37:25.218581+00	9853244b-1207-4535-9d52-80db539259bd	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:25.218106+00	\N	\N	\N	\N	\N
6204	monitor	Retry Test 2	\N	704579	2025-11-14 03:37:25.227491+00	d326c08f-a377-482d-9656-752ca2e2b816	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:25.227066+00	\N	\N	\N	\N	\N
6206	monitor	Expiry Test 032290	\N	032290	2025-11-14 03:37:32.513669+00	82db3c63-7508-48bc-88fb-972bd2f05bdd	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:32.513181+00	\N	\N	\N	\N	\N
6207	monitor	Retry Test 0	\N	666718	2025-11-14 03:37:32.551581+00	0fd2e253-0412-4bf1-a361-c72437cf5600	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:32.551092+00	\N	\N	\N	\N	\N
6208	monitor	Retry Test 1	\N	074376	2025-11-14 03:37:32.560508+00	2a31e9af-fd65-4b32-901b-ff5648667e95	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:32.560041+00	\N	\N	\N	\N	\N
6209	monitor	Retry Test 2	\N	906612	2025-11-14 03:37:32.569207+00	a0c603ef-5559-43d3-a631-9af767ad5df9	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 03:27:32.568757+00	\N	\N	\N	\N	\N
6199	monitor	Test Device 007910	4	007910	2025-11-14 03:36:05.010012+00	test-uuid-007910	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	released	2025-11-14 03:26:19.664765+00	0	t	101	lobby	t	limited	2025-11-14 03:26:05.009468+00	2025-11-14 17:57:43.576606+00	\N	\N	\N	\N
6194	monitor	Test Monitor 898137	4	898137	2025-11-14 03:34:57.296287+00	63fd6658-7cd9-49e8-abcf-29e189ec616e	\N	browser	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	released	2025-11-14 03:24:57.319203+00	0	t	101	lobby	t	limited	2025-11-14 03:24:57.295787+00	2025-11-14 17:59:57.256389+00	\N	\N	\N	\N
6210	monitor	New Device	\N	295802	2025-11-14 18:28:55.335057+00	\N	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 18:18:55.334655+00	\N	\N	\N	\N	\N
6211	monitor	Test Device - Integration	4	819675	2025-11-14 18:29:10.262407+00	\N	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	released	2025-11-14 18:19:10.276827+00	0	t	\N	guest_room	t	limited	2025-11-14 18:19:10.261879+00	2025-11-14 18:19:16.801566+00	\N	\N	\N	\N
6212	monitor	Manual Test Device - Reactivated	4	181332	2025-11-14 18:34:25.207099+00	\N	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-14 18:29:13.095069+00	0	t	\N	guest_room	t	limited	2025-11-14 18:24:25.20657+00	2025-11-14 18:29:13.094477+00	\N	\N	\N	\N
6213	monitor	New Device	\N	999888	2025-11-14 19:30:59.669594+00	test-fp-123456	\N	test	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-14 19:20:59.664578+00	\N	\N	\N	\N	\N
6214	monitor	New Device	\N	999111	2025-11-15 02:08:53.844172+00	fp-test-persistence	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 01:58:53.843091+00	\N	\N	\N	\N	\N
6215	monitor	New Device	\N	111111	2025-11-15 02:17:11.568767+00	fp-test-flow	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 02:07:11.567557+00	\N	\N	\N	\N	\N
6216	monitor	New Device	\N	111222	2025-11-15 02:21:21.938595+00	fp-test-consistency-1763172681	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 02:11:21.93747+00	\N	\N	\N	\N	\N
6217	monitor	New Device	\N	999999	2025-11-15 02:38:38.231933+00	fp-debug-test	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 02:28:38.230877+00	\N	\N	\N	\N	\N
6218	monitor	Test Player Chrome	4	371952	2025-11-15 02:42:20.455618+00	fp-00005c719b3c	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2025-11-15 02:40:19.420209+00	0	t	101	guest_room	t	limited	2025-11-15 02:32:20.45464+00	2025-11-15 02:40:19.419687+00	\N	\N	\N	\N
7649	monitor	New Device	\N	873519	2025-11-15 03:47:02.338309+00	fp-00002d52fe8f	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 03:37:02.337164+00	\N	\N	\N	\N	\N
7650	monitor	Test Device Manual #7650	4	745820	2025-11-16 04:39:43.082779+00	fp-00004f187301	\N	Chrome	1920	1080	1182	943	1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	4g	6.65	\N	\N	active	2025-11-18 01:56:08.958124+00	0	t	101	guest_room	t	limited	2025-11-15 03:40:17.439807+00	2025-11-18 01:56:08.956967+00	\N	\N	\N	\N
7651	monitor	New Device	\N	902964	2025-11-17 14:59:28.117497+00	fp-0000623a4a3e	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 06:36:43.206466+00	2025-11-17 14:49:28.116232+00	\N	\N	\N	\N
7654	monitor	Playwright Test Device	4	815636	2025-11-16 12:04:35.825238+00	fp-000053b5536b	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	\N	0	t	\N	guest_room	t	limited	2025-11-15 14:44:33.678292+00	2025-11-16 11:55:52.494814+00	\N	\N	\N	5
7647	monitor	New Device	\N	590485	2025-11-15 03:30:44.312175+00	fp-00004f5ab713	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 03:20:44.311125+00	\N	\N	\N	\N	\N
7648	monitor	New Device	\N	184239	2025-11-15 03:41:55.249473+00	fp-000076ff555a	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 03:31:55.248463+00	\N	\N	\N	\N	\N
7652	monitor	New Device	\N	124929	2025-11-15 09:17:47.869019+00	fp-00006ac5159b	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 09:07:47.867905+00	\N	\N	\N	\N	\N
7653	monitor	New Device	\N	550329	2025-11-15 09:19:26.952277+00	fp-00006f283032	\N	Chrome	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	pending	\N	0	t	\N	guest_room	t	limited	2025-11-15 09:09:26.95128+00	\N	\N	\N	\N	\N
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.organizations (id, name, pin, description, address, contact_email, contact_phone, logo_url, is_active, created_at, updated_at, max_devices, max_users, settings) FROM stdin;
4	TestOrg2	11223344	Test	Test	test@example.com	1234567890	\N	t	2025-11-05 00:08:46.240858+00	\N	10	5	{}
5	TestAuditOrg	12345678	Test Audit Logging	\N	\N	\N	\N	t	2025-11-05 13:38:35.735275+00	\N	10	5	{}
8	HotelTestOrg	999888	Hotel Test Organization for Multi-Tenant Testing	\N	\N	\N	\N	t	2025-11-13 01:52:52.397008+00	\N	10	5	{}
9	Updated_Org_1763024487	\N	\N	\N	\N	\N	\N	t	2025-11-13 09:01:29.859502+00	2025-11-13 09:01:29.889463+00	10	5	{}
10	Duplicate PIN Test	\N	\N	123 Test Street, Test City	\N	\N	\N	t	2025-11-13 09:01:29.906151+00	\N	10	5	{}
11	TestOrg1_1763026309	\N	\N	Test Address 1	\N	\N	\N	t	2025-11-13 09:31:50.343999+00	\N	10	5	{}
12	TestOrg2_1763026309	\N	\N	Test Address 2	\N	\N	\N	t	2025-11-13 09:31:50.357597+00	\N	10	5	{}
13	TEST_ORG_CONTENT_TAG	\N	\N	\N	\N	\N	\N	t	2025-11-13 12:20:26.736678+00	\N	10	5	{}
14	TEST_ORG_DEVICE_PLAYLIST	\N	\N	\N	\N	\N	\N	t	2025-11-13 12:20:26.754465+00	\N	10	5	{}
15	TEST_ORG_SCHEDULE	\N	\N	\N	\N	\N	\N	t	2025-11-13 12:20:26.769248+00	\N	10	5	{}
16	TEST_ORG_PMS_ANALYTICS	\N	\N	\N	\N	\N	\N	t	2025-11-13 12:20:26.782427+00	\N	10	5	{}
20	Test Tenant Organization	\N	Organization for testing purposes	Test Address 123	test@tenant.com	+62-812-3456-7890	\N	t	2025-11-14 07:05:19.401828+00	\N	10	5	{}
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.password_reset_tokens (id, user_id, token_hash, email, expires_at, created_at, consumed_at) FROM stdin;
\.


--
-- Data for Name: playlist_assignments; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.playlist_assignments (id, playlist_id, device_id, tag_id, created_at) FROM stdin;
\.


--
-- Data for Name: playlist_contents; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.playlist_contents (id, playlist_id, content_id, order_index, duration, created_at) FROM stdin;
1	5	6	0	15	2025-11-16 11:33:14.99449+00
2	5	7	1	10	2025-11-16 11:33:28.132284+00
3	5	8	2	10	2025-11-16 11:33:28.132284+00
4	5	9	3	10	2025-11-16 11:33:28.132284+00
5	5	10	4	10	2025-11-16 11:33:28.132284+00
\.


--
-- Data for Name: playlist_widgets; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.playlist_widgets (id, playlist_id, widget_id, "position", display_duration, z_index, created_at) FROM stdin;
\.


--
-- Data for Name: playlists; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.playlists (id, name, description, is_active, priority, schedule, organization_id, created_by_id, created_at, updated_at, deleted_at, is_default, is_pms_template) FROM stdin;
6	Morning Show	Morning content playlist	t	0	{}	4	9	2025-11-13 12:22:20.629831+00	\N	\N	f	f
7	Test Playlist	test	t	0	{}	4	9	2025-11-13 12:22:53.39275+00	\N	\N	f	f
8	Morning Show	Morning content playlist	t	0	{}	4	9	2025-11-13 12:31:37.321501+00	\N	\N	f	f
9	Morning Show	Morning content playlist	t	0	{}	4	9	2025-11-13 12:32:30.342894+00	\N	\N	f	f
10	Morning Playlist	Content for morning	t	0	{}	4	9	2025-11-13 12:38:32.965441+00	\N	\N	f	f
11	Evening Playlist	Content for evening	t	0	{}	4	9	2025-11-13 12:38:32.979115+00	\N	\N	f	f
12	Morning Playlist	Content for morning	t	0	{}	4	9	2025-11-13 12:40:16.38686+00	\N	\N	f	f
13	Evening Playlist	Content for evening	t	0	{}	4	9	2025-11-13 12:40:16.402203+00	\N	\N	f	f
14	Morning Playlist	Content for morning	t	0	{}	4	9	2025-11-13 12:42:01.286948+00	\N	\N	f	f
15	Evening Playlist	Content for evening	t	0	{}	4	9	2025-11-13 12:42:01.302715+00	\N	\N	f	f
16	Morning Playlist	Content for morning	t	0	{}	4	9	2025-11-13 12:43:14.525137+00	\N	\N	f	f
17	Evening Playlist	Content for evening	t	0	{}	4	9	2025-11-13 12:43:14.541675+00	\N	\N	f	f
19	Global Playlist	For all devices	t	0	{}	4	9	2025-11-13 12:43:14.640317+00	\N	\N	f	f
5	FinalTest_Playlist_1763027167	Testing after schema fixes	t	0	{}	4	9	2025-11-13 09:46:07.95946+00	2025-11-16 11:36:49.079192+00	\N	f	f
22	Manual_Upload_Test_1763361510	\N	t	0	{}	4	9	2025-11-17 06:38:32.920505+00	\N	\N	f	f
23	Video Test Playlist - 1763389404023	Playlist for testing video playback	t	0	{}	4	9	2025-11-17 14:23:24.549894+00	\N	\N	f	f
\.


--
-- Data for Name: pms_configurations; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.pms_configurations (id, organization_id, api_key, is_active, last_synced_at, sync_interval_minutes, created_by_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: pms_guests; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.pms_guests (id, organization_id, guest_name, room_number, checkin_date, checkout_date, email, phone, country, reservation_no, synced_at, created_at, updated_at, title, balance, loyalty_level, language, special_requests) FROM stdin;
\.


--
-- Data for Name: pms_rooms; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.pms_rooms (id, organization_id, room_number, room_type, status, floor, bed_type, max_occupancy, synced_at, last_updated, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.roles (id, name, description, organization_id, is_system_role, permissions, created_at, updated_at) FROM stdin;
1	SUPER_ADMIN	System administrator with full access to all organizations	\N	t	{"tags": ["create", "read", "update", "delete"], "users": ["create", "read", "update", "delete"], "devices": ["create", "read", "update", "delete"], "contents": ["create", "read", "update", "delete"], "settings": ["read", "update"], "analytics": ["read"], "playlists": ["create", "read", "update", "delete"], "audit_logs": ["read"], "organizations": ["create", "read", "update", "delete"]}	2025-11-09 17:28:48.672175+00	\N
2	ADMIN	Organization administrator with full organization access	\N	t	{"tags": ["create", "read", "update", "delete"], "users": ["create", "read", "update", "delete"], "devices": ["create", "read", "update", "delete"], "contents": ["create", "read", "update", "delete"], "settings": ["read", "update"], "analytics": ["read"], "playlists": ["create", "read", "update", "delete"]}	2025-11-09 17:28:48.672175+00	\N
3	CONTENT_MANAGER	Content manager with content and playlist management	\N	t	{"tags": ["create", "read", "update"], "devices": ["read"], "contents": ["create", "read", "update", "delete"], "analytics": ["read"], "playlists": ["create", "read", "update", "delete"]}	2025-11-09 17:28:48.672175+00	\N
4	VIEWER	Read-only access to view content and devices	\N	t	{"tags": ["read"], "users": ["read"], "devices": ["read"], "contents": ["read"], "analytics": ["read"], "playlists": ["read"]}	2025-11-09 17:28:48.672175+00	\N
\.


--
-- Data for Name: schedules; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.schedules (id, organization_id, name, description, playlist_id, start_date, end_date, start_time, end_time, recurrence_type, recurrence_pattern, exceptions, priority, is_active, created_by_id, created_at, updated_at, device_ids, tag_ids, applies_to_all) FROM stdin;
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.tags (id, tag_name, description, color, organization_id, created_at, priority, assigned_playlist_id) FROM stdin;
2	TestTagUpdated	Updated Description	#EF4444	4	2025-11-05 18:06:55.718619+00	50	\N
3	FixTest2	Testing fixes	#10B981	4	2025-11-06 00:30:31.592829+00	50	\N
4	AuditTestTag	Testing audit logging	#FF6B6B	4	2025-11-06 00:42:32.327057+00	50	\N
5	FinalAuditTestUpdated	Testing complete audit	#FF6B6B	4	2025-11-06 01:03:03.710877+00	50	\N
6	DeploymentTest	Testing after deployment	#3B82F6	4	2025-11-06 01:19:38.886044+00	50	\N
7	TestTag_1763026577	\N	#3B82F6	4	2025-11-13 09:36:17.714314+00	50	\N
8	TestTag2_1763026577	\N	#00FF00	4	2025-11-13 09:36:17.733319+00	50	\N
9	TestTag_1763027068	\N	#FF5733	4	2025-11-13 09:44:29.172711+00	50	\N
\.


--
-- Data for Name: templates; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.templates (id, organization_id, name, description, template_type, content, variables, preview_data, is_active, created_by_id, created_at, updated_at) FROM stdin;
1	4	Test_Template_1763030701	Test HTML template	html	<div>Welcome {{guest_name}}! Room: {{room_number}}</div>	null	null	t	9	2025-11-13 10:45:02.243293	2025-11-13 10:45:02.243293
\.


--
-- Data for Name: translations; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.translations (id, organization_id, entity_type, entity_id, language_code, field_name, translated_value, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.user_sessions (id, user_id, organization_id, session_token, refresh_token, ip_address, user_agent, device_info, created_at, last_activity_at, expires_at, revoked_at, session_type) FROM stdin;
110	9	4	53ab406ccd24cfb3b314ed1669f881201d938f2ef387389f82464949a334f8e1	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 02:08:08.871114+00	2025-11-14 02:08:08.871114+00	2025-12-14 02:08:09.095957+00	\N	web
1	9	4	e63f9e90a86e6a1e7e7066447ed301fb20f16a9022e80375fe96cc4f695abe3a	\N	192.168.5.172	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}	2025-11-09 19:17:05.128074+00	2025-11-09 19:17:05.128074+00	2025-12-09 19:17:05.345513+00	2025-11-09 19:18:21.841484+00	web
129	9	4	4b6f92928a56edd4b6a0bcd3bb3e7bfb409a70c97de7f95019ee7ef64a3c8ade	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:23:16.940003+00	2025-11-14 03:23:16.940003+00	2025-12-14 03:23:17.142049+00	\N	web
145	9	4	6902961c5809ddffb71e928c4449c8ce2173bfa7e2045270fb5a110909dd85b8	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:50:16.767626+00	2025-11-14 03:50:16.767626+00	2025-12-14 03:50:16.98854+00	\N	web
146	9	4	7c14e30b5a499fc8a22558785a59a33a2d002bd32b97c9e52cda4002e9e9b0da	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:50:29.26529+00	2025-11-14 03:50:29.26529+00	2025-12-14 03:50:29.469497+00	\N	web
138	9	4	88ac20a3c83e98038c6c362b7b925a79924214a0119628886f31aa3db16d5703	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:28:07.743643+00	2025-11-14 03:28:08.002202+00	2025-12-14 03:28:07.946196+00	\N	web
147	9	4	96296f1d0b8c97ebc6b1334f77b98c18d2286f8a9d26de5df644fda25a3bf7b5	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:50:38.446203+00	2025-11-14 03:50:38.446203+00	2025-12-14 03:50:38.649668+00	\N	web
215	9	4	8a641b4ba79656e9b04e01f5fdd2cabbac32a669317857468baf9d89290acb31	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-15 19:59:55.685941+00	2025-11-15 19:59:55.685941+00	2025-12-15 19:59:55.908097+00	\N	web
162	9	4	9be64810d9f47aeeae798a5d964cb63ccb2799569b3ebf98ce606d1ddbd7376c	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:55:05.600945+00	2025-11-14 05:55:05.600945+00	2025-12-14 05:55:05.805352+00	\N	web
172	28	5	5bfc3218a17b9f8f0b3116cf85394d28fea8e92346f5991a16b46905b3a25556	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:02:13.074672+00	2025-11-14 06:02:13.074672+00	2025-12-14 06:02:13.276168+00	\N	web
173	9	4	717a20a59a7b31596e1278a0b474cf95d716d37f50ccc61aa9169eaddb368a53	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:02:13.299274+00	2025-11-14 06:02:13.299274+00	2025-12-14 06:02:13.500562+00	\N	web
130	9	4	4e0893ec331385f8018c879f403abc2058f1887a844d42423714751f44132258	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:23:46.760871+00	2025-11-14 03:23:47.15387+00	2025-12-14 03:23:46.961263+00	\N	web
174	9	4	475010d46a369e0480e397dfc6da2975db87db5a962fbe2d954304f5b14cd21b	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:06:00.423584+00	2025-11-14 06:06:00.639498+00	2025-12-14 06:06:00.625625+00	\N	web
179	9	4	b9f0ea4686bde3c91ad2b55c72c72649b4be90922bd12c56154e8a856e9df86b	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 06:23:51.317308+00	2025-11-14 06:24:40.14511+00	2025-12-14 06:23:51.520634+00	\N	web
176	29	5	fc162540f169ca33175802b7ffe98c623c7ce9aec8a94d053c684ee98d92d3ae	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:12:44.930647+00	2025-11-14 06:12:44.930647+00	2025-12-14 06:12:45.131273+00	2025-11-14 06:12:45.364168+00	web
178	9	4	21f25a155ebe9175704413a5c7c2eacc570b5743b08be12fb1092723c1b5bef4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:12:48.547035+00	2025-11-14 06:12:48.547035+00	2025-12-14 06:12:48.748808+00	\N	web
196	9	4	492499610738df09c2d18c13a84cfadb8e2ad2de6c0de7d411dadf64d135042e	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 17:29:23.377245+00	2025-11-14 17:59:19.554769+00	2025-12-14 17:29:23.579335+00	\N	web
193	30	20	3b24a36e4717e94ec186aa643ebca93fdd2e194fb527897af0db044524f22f4b	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:11:24.320331+00	2025-11-14 07:11:24.603977+00	2025-12-14 07:11:24.542564+00	\N	web
113	9	4	540aa6e12b2d855696ef99a4bf05f5c707e174f29a59c17d6d935370ad891845	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 03:16:45.680908+00	2025-11-14 03:42:31.918667+00	2025-12-14 03:16:45.885679+00	\N	web
201	9	4	03dde8674917146ed976a75e6e6b1370fcf077ea78eb6e4f22f15d23f42cdfbb	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 17:59:57.029592+00	2025-11-14 17:59:57.278023+00	2025-12-14 17:59:57.22868+00	\N	web
202	9	4	97f5127c06498032a178a8c18d4ba2bdcd192c27485d6242f437aa78fee8f537	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:18:22.367246+00	2025-11-14 18:18:22.588315+00	2025-12-14 18:18:22.574613+00	\N	web
203	9	4	674a3d3312ecbc411ba906433dd90109b4137ac02a55cbf4fe470b487e8b67a4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:18:38.878006+00	2025-11-14 18:18:38.878006+00	2025-12-14 18:18:39.082333+00	\N	web
204	9	4	44e8bbf6385156b78f4bc7534d1a921497568065fffa64aeba836da36133b78d	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:18:55.12049+00	2025-11-14 18:18:55.12049+00	2025-12-14 18:18:55.321508+00	\N	web
205	9	4	11d23a5e37cd92067772bca55fc070885ba4d7ee5c5dc3af48ccdb1a22565683	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:19:10.044122+00	2025-11-14 18:19:10.274289+00	2025-12-14 18:19:10.252005+00	\N	web
206	9	4	fb54c76b45dc58612ec02453ed287232b4e3aa8c408598e001e874ca34076cb4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:19:16.566225+00	2025-11-14 18:19:16.82127+00	2025-12-14 18:19:16.769286+00	\N	web
207	9	4	e398340526c51430733e0d2d065d5ecb52e2856258cdd8ec0c026fd7ade8c5b8	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:24:49.264391+00	2025-11-14 18:24:49.264391+00	2025-12-14 18:24:49.468512+00	\N	web
208	9	4	8918d5687f3ff980b73331d3008f3ae6749c7aca1b0236d7a1553f17ef80305a	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:25:16.360068+00	2025-11-14 18:25:16.575317+00	2025-12-14 18:25:16.561628+00	\N	web
209	9	4	89e784adbaa89f4e127107002b81e6b7a353bbfe8a45b0cfd8010821943b20fc	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:25:34.221895+00	2025-11-14 18:25:34.432421+00	2025-12-14 18:25:34.422484+00	\N	web
197	9	4	ed5657efeb6154a6e62033babcc97addae4d3d711700cd6e009bbe1026aeeffe	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 17:53:50.579117+00	2025-11-14 17:53:50.817017+00	2025-12-14 17:53:50.782312+00	\N	web
111	9	4	c158ff9a063474fdd30b99359c8ba117ce224bbade812b7f68e4a01609eb291c	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 02:53:24.09496+00	2025-11-14 02:53:24.09496+00	2025-12-14 02:53:24.317504+00	\N	web
144	9	4	cdb50ae2a8122decf698b8e67f97d85ae9670a1de20c276694a6842c5c944b24	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 03:47:25.03576+00	2025-11-14 03:49:55.713655+00	2025-12-14 03:47:25.237703+00	\N	web
139	9	4	163a03f28d7ecc07458470fa3a053d5b9ea482838300887b8bf51b07073ed431	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:28:12.900301+00	2025-11-14 03:28:13.262217+00	2025-12-14 03:28:13.10046+00	\N	web
149	9	4	46c453a0eefc160a209f687ea7443321281683142ba56eba831c607169b654b7	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 04:20:34.803532+00	2025-11-14 04:20:34.803532+00	2025-12-14 04:20:35.026357+00	\N	web
150	9	4	a30962305aa0660455eee0226e3c97bbd617de390019a010d35c5e87022e9c69	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 04:31:34.396911+00	2025-11-14 04:31:34.396911+00	2025-12-14 04:31:34.598349+00	\N	web
151	9	4	85359d828ca711ff3190eed2865fa70de946c0f2caba7531affafd7f5561b2b6	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 04:39:09.73695+00	2025-11-14 04:39:09.73695+00	2025-12-14 04:39:09.939454+00	\N	web
152	9	4	5fa7c1be8af36d0f69e1bd3ba7e0f133f95dc992eac63340ba23f373d589463a	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:29:43.400559+00	2025-11-14 05:29:43.400559+00	2025-12-14 05:29:43.601595+00	\N	web
164	26	5	47afce6392e8d598054e316c18ae43ffb8f641eccf512956687c597c56030507	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:55:09.606079+00	2025-11-14 05:55:09.606079+00	2025-12-14 05:55:09.867291+00	\N	web
177	29	5	f209905a3de3e647a946eb3d6056ce82d6d3c59fcfeeba5ff582ebdc4c51085a	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:12:48.323572+00	2025-11-14 06:12:48.323572+00	2025-12-14 06:12:48.527628+00	\N	web
216	9	4	b29329e0882ac27fe190c5116e3ea2dac187d4aea6fd302f9f1b59f316563201	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-16 04:09:06.892993+00	2025-11-16 04:09:06.892993+00	2025-12-16 04:09:07.110243+00	\N	web
131	9	4	5f1f6550bdd43376ccc66b11f6f500612a2e72483676b653a17acc2ffc43f3fa	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:24:57.043108+00	2025-11-14 03:24:58.516308+00	2025-12-14 03:24:57.267123+00	\N	web
180	9	4	0f3cabecaecc9dd1288d77cb86ab1a4960f6c5b81e09c14dc6262b31e186bfc5	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 06:25:26.970164+00	2025-11-14 06:25:34.230093+00	2025-12-14 06:25:27.194312+00	\N	web
181	9	4	7b67cfd6ba11994ee38785a0abeecf4949bede10d0b0c1cf4e53d0866c1762fa	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 07:01:43.318405+00	2025-11-14 07:01:43.318405+00	2025-12-14 07:01:43.525206+00	\N	web
182	9	4	66006a6e961dc15ac67db70c4ec3d6de1dad5b8159343bb68e3d88042e3e042b	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:02:19.012495+00	2025-11-14 07:02:19.012495+00	2025-12-14 07:02:19.214874+00	\N	web
183	24	\N	80c44700372273536d2360cbb01d9c0a52b66f7836fdc9ba6000ede353a87903	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:02:19.325381+00	2025-11-14 07:02:19.325381+00	2025-12-14 07:02:19.528999+00	\N	web
132	9	4	3f195e67476ea9870e563b7691b7fe86e2c8618c96432291a3da99970b3e01ca	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:25:12.44199+00	2025-11-14 03:25:13.123223+00	2025-12-14 03:25:12.644467+00	\N	web
2	9	4	2fcfe249d55cd0ef1426715f14f323c21c3349f3c96857f795f950327f8732fc	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-09 19:28:30.391097+00	2025-11-09 19:28:30.391097+00	2025-12-09 19:28:30.586029+00	2025-11-12 14:46:42.999491+00	web
3	9	4	5b570c02e6a0fade78eed5515125e13fc91409f8e888ddf7bf484483651dc954	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-10 02:39:22.444933+00	2025-11-10 02:39:22.444933+00	2025-12-10 02:39:22.667232+00	2025-11-12 14:46:42.999491+00	web
4	9	4	f576bb683019d3710886e54dfd8931edc4344e85bb05095ce6ced62b16421f5d	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-10 02:44:52.940855+00	2025-11-10 02:44:52.940855+00	2025-12-10 02:44:53.142236+00	2025-11-12 14:46:42.999491+00	web
5	9	4	6c0d8aaa8ce4484ecf7c794e06ef2591dbf4a89a4f81e32230bfe589351e08b5	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-10 03:36:29.460377+00	2025-11-10 03:36:29.460377+00	2025-12-10 03:36:29.659753+00	2025-11-12 14:46:42.999491+00	web
198	9	4	50517dc918ad812f969fbfd96d069422dcb31fa2bc33d13af7fffee237b241d3	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 17:54:14.571885+00	2025-11-14 17:54:14.833525+00	2025-12-14 17:54:14.795473+00	\N	web
133	9	4	f6dba9dd98c6e0206462ad21e4c7a306816b919e3a505114c262bddb02b243de	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:25:24.328086+00	2025-11-14 03:26:19.662221+00	2025-12-14 03:25:24.53066+00	\N	web
210	9	4	d1887bf7b073b3fa5bbdaa5aad58251889c83744fbb31d7613eb4dfaf35e44df	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:26:03.011561+00	2025-11-14 18:26:03.254056+00	2025-12-14 18:26:03.213155+00	\N	web
217	9	4	4441c9c8f6f2efadfcd5cb17ed4573b93a4a4f426fa67b71db67495e5343c0ec	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-16 04:30:36.469136+00	2025-11-16 04:34:01.909274+00	2025-12-16 04:30:36.671275+00	\N	web
211	9	4	2434f27b1e6cda9ff9918e048892902a021ac30d2179ba24dfd1c782e563132e	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 18:29:10.763193+00	2025-11-14 18:29:13.089332+00	2025-12-14 18:29:10.968465+00	\N	web
194	30	20	8fa7776654f2b9b5f6b8c01381267f6f407e7c3412dbb9037aed63a2037133a1	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:12:20.005564+00	2025-11-14 07:12:20.35336+00	2025-12-14 07:12:20.229047+00	\N	web
223	9	4	f479818f63e4cbfa72dc906fc5d18ba95e1d19afd99339802c736c17e88bad0a	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 13:02:14.960192+00	2025-11-17 13:15:21.264019+00	2025-12-17 13:02:15.174922+00	\N	web
195	9	4	7fe80f712230b1d1ce94cf39518b5ec9b4c89be9f8e3f10a9fc1146c6d9fdabf	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 09:28:51.031544+00	2025-11-14 09:45:50.534751+00	2025-12-14 09:28:51.231996+00	\N	web
6	9	4	4aa1142745f0d6fabb8298ad8973b6009070521aa93e366911a6a6f7368206b6	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-10 03:38:23.591845+00	2025-11-10 03:38:23.591845+00	2025-12-10 03:38:23.798881+00	2025-11-12 14:46:42.999491+00	web
7	9	4	7384d673c0159c88977a64955a51d1f29d398328a1d09d5e28a859aaa3126a0c	\N	192.168.5.172	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-10 13:59:41.314096+00	2025-11-10 13:59:41.314096+00	2025-12-10 13:59:41.515716+00	2025-11-12 14:46:42.999491+00	web
8	9	4	38ee4c49fdb6b34be1097c46558bd3be30fe4f2d40e722c21b5af2eb16f13f2f	\N	192.168.5.172	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-10 14:47:19.310229+00	2025-11-10 14:47:19.310229+00	2025-12-10 14:47:19.510922+00	2025-11-12 14:46:42.999491+00	web
9	9	4	5426e3027abd640cfdaf78dc47b28c6d0e196f55412b44d4703590b0893e8a8d	\N	192.168.5.172	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-10 15:26:13.81875+00	2025-11-10 15:26:13.81875+00	2025-12-10 15:26:14.02306+00	2025-11-12 14:46:42.999491+00	web
10	9	4	57ee613a295e0a169b2eeb347102f053546351b35c434d542f81589f4894c4f8	\N	192.168.5.172	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 08:30:28.248126+00	2025-11-11 08:30:28.248126+00	2025-12-11 08:30:28.465289+00	2025-11-12 14:46:42.999491+00	web
11	9	4	3a55426865f07f34b8f441099211416ab8ce3fba60bdd063ef57ab9fae6e9226	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 08:53:21.633007+00	2025-11-11 08:53:21.633007+00	2025-12-11 08:53:21.83565+00	2025-11-12 14:46:42.999491+00	web
12	9	4	5148bd6fedc730c60465d41cffad57374125464eb1996c0c212a75fff8091b4e	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 10:37:59.561008+00	2025-11-11 10:37:59.561008+00	2025-12-11 10:37:59.760673+00	2025-11-12 14:46:42.999491+00	web
13	9	4	b0115f2c1aeae9ea1085efce30714a87ab69dc7aa416ced0ea2f4b4607c39058	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 13:39:44.727904+00	2025-11-11 13:39:44.727904+00	2025-12-11 13:39:44.924174+00	2025-11-12 14:46:42.999491+00	web
14	9	4	7c4b643a7c7e5fa99978fd63e2718ec81e118ac008f82cb4cc9b018f6bb85b38	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 13:46:44.051246+00	2025-11-11 13:46:44.051246+00	2025-12-11 13:46:44.279642+00	2025-11-12 14:46:42.999491+00	web
15	9	4	9f9660fec1c6662a0f5bc788e10b2c32259bdb920ea9876191ab577f68a7b774	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 14:50:39.352813+00	2025-11-11 14:50:39.352813+00	2025-12-11 14:50:39.551089+00	2025-11-12 14:46:42.999491+00	web
16	9	4	db5a875ff4916fba22662e56bf85beb081099d0ad5ad3543cd1ea6ac993d04d5	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 15:35:02.454337+00	2025-11-11 15:35:02.454337+00	2025-12-11 15:35:02.658163+00	2025-11-12 14:46:42.999491+00	web
17	9	4	1b56c8f8447fecbbe35ca2f78c0431dfb9754122f198f5b224c2e9e107485834	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 16:07:08.045448+00	2025-11-11 16:07:08.045448+00	2025-12-11 16:07:08.242476+00	2025-11-12 14:46:42.999491+00	web
18	9	4	fc447e4296ec9ce5795d485c42f942c8322665c4a36760176c86ef36613f6ecc	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-11 16:38:40.710858+00	2025-11-11 16:38:40.710858+00	2025-12-11 16:38:40.906585+00	2025-11-12 14:46:42.999491+00	web
19	9	4	9787562a4f489b52f18a28c32194f5344ee6f65a93680e12ad1615749cb564fa	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-12 00:17:01.075563+00	2025-11-12 00:17:01.075563+00	2025-12-12 00:17:01.296036+00	2025-11-12 14:46:42.999491+00	web
20	9	4	ba02c8fcf637dd883d78104d4391c7151a116f25a2331626d59a807426f3d4f9	\N	172.18.0.7	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-12 01:11:44.580764+00	2025-11-12 01:11:44.580764+00	2025-12-12 01:11:44.780791+00	2025-11-12 14:46:42.999491+00	web
21	9	4	d3d0cda464b08ccbc0167d6c2e70a88718bfab54531f0c09f33f5c47ac5d64c4	\N	172.18.0.11	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-12 02:17:26.244053+00	2025-11-12 02:17:26.244053+00	2025-12-12 02:17:26.468932+00	2025-11-12 14:46:42.999491+00	web
22	9	4	cbd7fedd61f128ec568b9c08c55222651236447879dc6aeae6d9ccef54bdcfd2	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-12 02:18:29.464426+00	2025-11-12 02:18:29.464426+00	2025-12-12 02:18:29.662501+00	2025-11-12 14:46:42.999491+00	web
23	9	4	9c28ce24d094b7e89aecf2d81e02f997764c173f551dbd4139e3b198e18be29b	\N	172.18.0.11	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-12 04:11:48.105444+00	2025-11-12 04:11:48.105444+00	2025-12-12 04:11:48.310507+00	2025-11-12 14:46:42.999491+00	web
24	9	4	32abee9a7e82af09e2102b49f56e83763eacc47ff632343e361855c52b927d73	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"}	2025-11-12 06:17:21.120687+00	2025-11-12 06:17:21.120687+00	2025-12-12 06:17:21.315347+00	2025-11-12 14:46:42.999491+00	web
106	9	4	e325ec87a510dcdbc7fc8e0c196edf1d4d45bec6d9084469eee243e469f00f83	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 23:59:32.423563+00	2025-11-13 23:59:32.423563+00	2025-12-13 23:59:32.619782+00	\N	web
25	9	4	3ee10dc9d6cb345dd8b9271ab49042091a933d44ed191ec41cd38592d304fd12	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 06:59:39.607457+00	2025-11-12 06:59:39.607457+00	2025-12-12 06:59:39.803124+00	2025-11-12 14:46:42.999491+00	web
26	9	4	c8b793f0c4f3eacddd81298447b2a4e5890f9a61a63c53f8d9df99b3a726cd4c	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 07:52:09.772175+00	2025-11-12 07:52:09.772175+00	2025-12-12 07:52:09.967644+00	2025-11-12 14:46:42.999491+00	web
27	9	4	4a9e16678819bf3c262e5b64719be7f09dd3fc72091b7eb42feac43ec3a11c47	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 08:54:36.912079+00	2025-11-12 08:54:36.912079+00	2025-12-12 08:54:37.109112+00	2025-11-12 14:46:42.999491+00	web
28	9	4	1da501086f23cffa4b0b07c8abf9c2488817d1e14b18c7922919e8955b57ebdd	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 09:24:43.283073+00	2025-11-12 09:24:43.283073+00	2025-12-12 09:24:43.483205+00	2025-11-12 14:46:42.999491+00	web
29	9	4	36b2a79b4a453e9ab17f4a2323483ffe1eac657a67eb8cf68b1057555daa3254	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 09:40:47.625343+00	2025-11-12 09:40:47.625343+00	2025-12-12 09:40:47.828098+00	2025-11-12 14:46:42.999491+00	web
30	9	4	45fb27d98c8215924253d04e02027a8f13ebe8c83f446c4fa78980c8aa1e4a82	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 10:13:20.414779+00	2025-11-12 10:13:20.414779+00	2025-12-12 10:13:20.613355+00	2025-11-12 14:46:42.999491+00	web
31	9	4	23d260b54774fd9211a819ae11e0601a22952b49cdfbc24e61d69a1b9992b5d1	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 10:14:06.331941+00	2025-11-12 10:14:06.331941+00	2025-12-12 10:14:06.530096+00	2025-11-12 14:46:42.999491+00	web
32	9	4	9317c03a3bdfde989079df86cb3435757c4c5f66bc6bca9ceec0d8ceb8b67ca5	\N	172.18.0.4	Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36	{"platform": "Linux", "user_agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36"}	2025-11-12 10:30:08.194655+00	2025-11-12 10:30:08.194655+00	2025-12-12 10:30:08.398562+00	2025-11-12 14:46:42.999491+00	web
33	9	4	2ba32abdaac4ce7c78123256202fbb818bb0ca525755bb4ba480700b7856b6ab	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 11:00:35.879689+00	2025-11-12 11:00:35.879689+00	2025-12-12 11:00:36.090466+00	2025-11-12 14:46:42.999491+00	web
34	9	4	30da967539707562f2746966031572085b103cf26d8d25329efdf37eda36fa4c	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 12:20:55.604327+00	2025-11-12 12:20:55.604327+00	2025-12-12 12:20:55.802664+00	2025-11-12 14:46:42.999491+00	web
35	9	4	e850a52b7b631b0d35f8fa21a39772cb9cd44ab6a509b0713ea9903db8f9840a	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 12:55:20.875858+00	2025-11-12 12:55:20.875858+00	2025-12-12 12:55:21.076266+00	2025-11-12 14:46:42.999491+00	web
36	9	4	ecf52a8adc9a4f17af7970723b6a9e13bc84ccd23951ca6017c65c4b4f6ce037	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 13:29:12.912412+00	2025-11-12 13:29:12.912412+00	2025-12-12 13:29:13.107313+00	2025-11-12 14:46:42.999491+00	web
37	9	4	44f5ba4580d5781224fb3bd158004211345e401f2326bb575e94dedf0651da65	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 13:59:58.835011+00	2025-11-12 13:59:58.835011+00	2025-12-12 13:59:59.031252+00	2025-11-12 14:46:42.999491+00	web
38	9	4	f1e0909e1f532b8fde054aa5f794b111bb766c3c0d0aaad4974cc47e18743b60	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 14:38:19.311295+00	2025-11-12 14:38:19.311295+00	2025-12-12 14:38:19.510694+00	2025-11-12 14:46:42.999491+00	web
39	9	4	1352486ee9fe0cc6aa5f1cd0752bc12c7adea1f9d3f557aed81f78764747736e	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 14:53:38.144307+00	2025-11-12 14:53:38.144307+00	2025-12-12 14:53:38.342569+00	\N	web
40	9	4	6c5645358d9746b61394c1f2859d95c904112edb621f3ee9d708727638ef9987	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 15:01:00.204405+00	2025-11-12 15:01:00.204405+00	2025-12-12 15:01:00.402029+00	\N	web
41	9	4	bdf49370a75602dd1dd0eb2e36d81593848c25daa189b89ca8cc387a3b5642ff	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 16:13:15.521656+00	2025-11-12 16:13:15.521656+00	2025-12-12 16:13:15.720233+00	\N	web
42	9	4	2b6ec878c90ab74c4800f2adbc5765a2c20fe3302f2bb03ec7ea43a222d04002	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 17:14:49.15616+00	2025-11-12 17:14:49.15616+00	2025-12-12 17:14:49.360473+00	\N	web
71	9	4	4d9e7ceaeaf926dee98ba12093b21292ecce845e7ec59e28c78af27fbd674b43	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:26:00.838678+00	2025-11-13 09:26:00.838678+00	2025-12-13 09:26:01.039+00	\N	web
43	9	4	bae47948583a050804d62411b0f13a5ac7735fbca64887db9d29b4755b6a2789	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-12 18:06:49.94429+00	2025-11-12 18:06:49.94429+00	2025-12-12 18:06:50.141608+00	\N	web
112	9	4	8e5d519b2c2137bc7974bf4dfa4a8275e21a21984fe54206111801b2959bd6de	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:06:12.298463+00	2025-11-14 03:06:12.298463+00	2025-12-14 03:06:12.517984+00	\N	web
153	9	4	67375c2966ca247377c6d732e30eeaed5181960547cf70882ec0f21e703176f6	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:32:07.5887+00	2025-11-14 05:32:07.5887+00	2025-12-14 05:32:07.811844+00	\N	web
165	9	4	fbe9ec5a9ad114458bb5dc4262600db38ba0ce31416ab31072aa42d3e40d5413	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:55:09.889826+00	2025-11-14 05:55:09.889826+00	2025-12-14 05:55:10.089291+00	\N	web
184	9	4	ef9b3f33aa2e3337a8501caa2aeafc4014027e5542e265fa03e4c67eb018937a	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:03:00.781152+00	2025-11-14 07:03:00.781152+00	2025-12-14 07:03:00.982023+00	\N	web
199	9	4	bf17d28537a331657c0f0a7f725a3045610b52c9dc35bde88025155894b7b634	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 17:54:41.563628+00	2025-11-14 17:54:41.818718+00	2025-12-14 17:54:41.786101+00	\N	web
114	9	4	cd898b5a62d955efda8550bc34a10b8943d1f14645083deb6f4f6d657f7ee077	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:18:01.683693+00	2025-11-14 03:18:01.683693+00	2025-12-14 03:18:01.886242+00	\N	web
214	9	4	0a416de1fa09524fef7fed44af282faddf202bd32888880f3cdac58f908a72f8	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-15 02:39:53.889101+00	2025-11-15 02:40:19.414401+00	2025-12-15 02:39:54.090404+00	\N	web
134	9	4	a4b07383d5952e2921ef23bd6301c3ab23a2d72f0da45b0d6f980ba361651afb	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:25:56.898157+00	2025-11-14 03:25:57.782553+00	2025-12-14 03:25:57.119081+00	\N	web
212	9	4	af12854cc41880aacdb6e4f5c5e916bfe6d825df58f035af8803c72d4a84238b	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-15 02:39:31.976446+00	2025-11-15 03:09:32.683732+00	2025-12-15 02:39:32.193981+00	\N	web
218	9	4	2ad1694cd62cbab8cd90369342d567980f614801d3c8a375eb195dac64d77b65	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-16 17:17:31.341044+00	2025-11-16 17:17:41.628328+00	2025-12-16 17:17:31.562771+00	\N	web
224	9	4	958921ab433b910c2093dbc175a4f02756300b5472748fa827cfa9448ff1f0ab	\N	192.168.5.172	node	{"platform": "unknown", "user_agent": "node"}	2025-11-17 13:41:15.495698+00	2025-11-17 13:41:15.741982+00	2025-12-17 13:41:15.712327+00	\N	web
225	9	4	e2262491d6510cb7abd030994d46def20a3252ddcafafa5a9dc05b80c81fdd7f	\N	172.16.9.237	node-fetch/1.0 (+https://github.com/bitinn/node-fetch)	{"platform": "unknown", "user_agent": "node-fetch/1.0 (+https://github.com/bitinn/node-fetch)"}	2025-11-17 14:23:23.909068+00	2025-11-17 14:23:24.568331+00	2025-12-17 14:23:24.105219+00	\N	web
140	9	4	8e00893bb8bf9db5f7a31382d3c55ff556536bcfde879542c4dddb95e4529cb1	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:32:39.831664+00	2025-11-14 03:32:40.217783+00	2025-12-14 03:32:40.052997+00	\N	web
44	9	4	1052c2184d46cf1b95545daf2c23d60c0ca64fb015289d844aed32a50ea033f4	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 01:08:02.839224+00	2025-11-13 01:08:02.839224+00	2025-12-13 01:08:03.042363+00	\N	web
45	9	4	f65dbbfbab9f1b36ef91a341e58053fb9d898e8a485ddf11f8fb686291336bd6	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 01:36:40.735928+00	2025-11-13 01:36:40.735928+00	2025-12-13 01:36:40.954082+00	\N	web
46	9	4	462c958edc70a7ffb308f13055fb42d1d3c1506d71bbdd0aab475cbb59713c4b	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 01:37:09.773203+00	2025-11-13 01:37:09.773203+00	2025-12-13 01:37:09.971896+00	\N	web
47	9	4	f5e9e5f6702d89aa313fa3fb88830139122775a4b4a90646908a3cf3fb4d71c6	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 01:44:32.929801+00	2025-11-13 01:44:32.929801+00	2025-12-13 01:44:33.147338+00	\N	web
48	9	4	c6c522e1a4715f832cc9535edb4c57f9e8dacafd4e86374b3a319ee134503d14	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 01:47:06.001691+00	2025-11-13 01:47:06.001691+00	2025-12-13 01:47:06.218349+00	\N	web
49	9	4	0713abc106b5d818c204e09a1caaa0029eb6f84a36bae5000261efd39a9e84a7	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 01:47:48.219571+00	2025-11-13 01:47:48.219571+00	2025-12-13 01:47:48.419528+00	\N	web
50	9	4	52296369cc727f74d18ea8c50928743e9777d66c2aeaf9b5bcae86ece3b36db2	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 01:48:39.524367+00	2025-11-13 01:48:39.524367+00	2025-12-13 01:48:39.747227+00	\N	web
51	9	4	258417fe71af84d26f26e7f8dc3f7f5c713426e50e721b921ce94b1f92040c73	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 01:51:27.936473+00	2025-11-13 01:51:27.936473+00	2025-12-13 01:51:28.13744+00	\N	web
52	11	8	2bcdddf367b1431018459421f73238c1ce52d76ca9f6c63c287700e22f6aeb18	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 01:53:28.980516+00	2025-11-13 01:53:28.980516+00	2025-12-13 01:53:29.185828+00	\N	web
115	9	4	89815d1b52a19ae886d78c195e5fc0ec2a24a96b0b8d129434cfb3ae900ac52e	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:18:06.327043+00	2025-11-14 03:18:06.327043+00	2025-12-14 03:18:06.528747+00	\N	web
53	9	4	73a4f8c9e8365fc0b6d0851e20811d2f1eaaf19b365cb44aa203b8cb0d67db5d	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 01:59:00.527711+00	2025-11-13 01:59:00.527711+00	2025-12-13 01:59:00.748915+00	2025-11-13 01:59:03.290662+00	web
54	11	8	04e099d7d005560b4d9cad394b8561026e806dae71f5afdc02ba8073a049da78	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 01:59:17.855552+00	2025-11-13 01:59:17.855552+00	2025-12-13 01:59:18.05979+00	\N	web
55	9	4	d1bb82214294e0ac6d2e148eeb95da8954eb6cfb50091c18300f12e97b3823d4	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 02:00:08.789691+00	2025-11-13 02:00:08.789691+00	2025-12-13 02:00:08.987855+00	\N	web
56	9	4	3d83599ff053499d96dc0775c5b9406099fd04a2e4929b2865cb4ae569358e8b	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 02:59:55.421911+00	2025-11-13 02:59:55.421911+00	2025-12-13 02:59:55.637326+00	\N	web
57	11	8	1585d40ff205c6f252b20994a1ea811365de97919b8d8fd6a48dbc570ad904fe	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 03:00:12.769904+00	2025-11-13 03:00:12.769904+00	2025-12-13 03:00:12.9686+00	\N	web
58	9	4	fa064db207d5d3aac9d34c0ec4de20747073dc09713d84fcba9dbf428ed925a1	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 03:22:17.331182+00	2025-11-13 03:22:17.331182+00	2025-12-13 03:22:17.548396+00	\N	web
59	9	4	460c9e919c8530ac6d3e75e16cb2bd1cfc77332a2d538a18baa3220ad03e3c21	\N	172.18.0.1	curl/7.81.0	{"platform": "unknown", "user_agent": "curl/7.81.0"}	2025-11-13 03:22:23.067892+00	2025-11-13 03:22:23.067892+00	2025-12-13 03:22:23.267238+00	\N	web
60	9	4	c38815d55d4df6198443a5f38b7f6594679dcf2238435d212d1da1b5a376109d	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 04:30:16.889735+00	2025-11-13 04:30:16.889735+00	2025-12-13 04:30:17.090686+00	\N	web
61	9	4	f79cd863121515043bb69b0e5522ad2bf2b3944e568c664943b8a3511b6f2284	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 05:16:55.588526+00	2025-11-13 05:16:55.588526+00	2025-12-13 05:16:55.805951+00	\N	web
62	9	4	df6ad708c60429ef40a0f1965a171c54e17cd63e391c59ae19f6f1133be29c2e	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 05:51:02.853487+00	2025-11-13 05:51:02.853487+00	2025-12-13 05:51:03.056359+00	\N	web
63	11	8	28d2c00a876207fe7286833765046f9843e5b9fb907b90c786318b5077748f49	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 06:30:53.424873+00	2025-11-13 06:30:53.424873+00	2025-12-13 06:30:53.620796+00	\N	web
64	9	4	777d6077979681765675d69b0e0d791f67bb215191f02866e17dcd16985b6e03	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 06:33:07.110476+00	2025-11-13 06:33:07.110476+00	2025-12-13 06:33:07.305696+00	\N	web
65	11	8	524b52c00ea50cba295a7d6a2485588d0c66e7ca5775a4f516ec1377bbe41405	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 08:39:15.982257+00	2025-11-13 08:39:15.982257+00	2025-12-13 08:39:16.185078+00	\N	web
117	9	4	6dcecb2e998aa0900a8a8b32735f3bcca371530a2614ddcf0f9befb116a0a9f3	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:18:38.436972+00	2025-11-14 03:18:38.436972+00	2025-12-14 03:18:38.64437+00	\N	web
66	9	4	604a9cca1fc074c593642ae285b5cbb4f9271dff91bf7e358af528a602039b86	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 08:41:43.214378+00	2025-11-13 08:41:43.214378+00	2025-12-13 08:41:43.410556+00	2025-11-13 08:42:07.130369+00	web
72	9	4	81c62c095aa18d37da278503c5d3d1c688caae87b9256ee70911c63c3d73bab9	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:31:11.265065+00	2025-11-13 09:31:11.265065+00	2025-12-13 09:31:11.471072+00	\N	web
74	9	4	da40f003ec9c7397e55cc485df123703b5c5de0b6435cbe5bdf151f5a1ef6850	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:34:35.989796+00	2025-11-13 09:34:35.989796+00	2025-12-13 09:34:36.186892+00	\N	web
75	9	4	d9840cc3c4fc0acc30004d09189300cae70dd3c83dedac1060175d68bbc66152	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:36:17.487801+00	2025-11-13 09:36:17.487801+00	2025-12-13 09:36:17.692697+00	\N	web
116	9	4	adb5457a845301e7ac870a5b707a198d5bafc9f102645e1531e95af773972a06	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:18:16.782304+00	2025-11-14 03:18:16.782304+00	2025-12-14 03:18:16.98739+00	\N	web
141	9	4	2d8cd187d147c842ca72446cbad08f06d8a49f1370cf88c70ce9ec1fc3b52fd5	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:34:59.296508+00	2025-11-14 03:34:59.296508+00	2025-12-14 03:34:59.520323+00	\N	web
154	9	4	0ad18df262817acd8e5fc0c48401659c660d01b4da485dd62d962fb97493c763	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:33:48.342744+00	2025-11-14 05:33:48.342744+00	2025-12-14 05:33:48.570626+00	\N	web
166	9	4	b11924c8853de7415f6300d3e14a36b7a74f650373ffa5b021fd803e3ad7df84	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:00:11.633789+00	2025-11-14 06:00:11.633789+00	2025-12-14 06:00:11.85523+00	\N	web
185	9	4	8030ea1e43b267148c9011df23a7396fa81f6334659ec04b27a798ab9611092f	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:04:31.383058+00	2025-11-14 07:04:31.383058+00	2025-12-14 07:04:31.605988+00	\N	web
167	27	5	89368359f429c6594134b9577d626e1775417572a508dbb7c4f994bc1bbbc288	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:00:12.121182+00	2025-11-14 06:00:12.121182+00	2025-12-14 06:00:12.321772+00	2025-11-14 06:00:12.553891+00	web
168	27	5	19d5b0b2b6387f31b391cd43dce5be27c290bf758478c3aaf8ece69c6204af21	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:00:15.721686+00	2025-11-14 06:00:15.721686+00	2025-12-14 06:00:15.923449+00	\N	web
135	9	4	fe4e45d4110480c1a91d78f15ca5d077a283e021f1839506c5520fbc6e356ccd	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:27:17.685352+00	2025-11-14 03:27:18.323387+00	2025-12-14 03:27:17.907567+00	\N	web
169	9	4	e28302e8d76a6031c3c4f903b6a3df4aa7cd73bda454f9578f0b479258b55c2f	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:00:15.94627+00	2025-11-14 06:00:15.94627+00	2025-12-14 06:00:16.148435+00	\N	web
213	9	4	897a70f7d315c9118bdaf7aceedc598259b6dc2947f9653b9aaaa3dc9a5b35fa	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-15 02:39:38.947321+00	2025-11-15 02:39:38.947321+00	2025-12-15 02:39:39.147495+00	\N	web
219	9	4	2c3de02d0c329317e9811b03fa62ce5d7fcdfd0727b394656285f603f22a3604	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 03:55:00.706176+00	2025-11-17 03:55:00.706176+00	2025-12-17 03:55:00.905735+00	\N	web
226	9	4	9789997818282809d5273809b4a18f96f3cf59125ead80158a76c5624e367a01	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 14:30:45.810321+00	2025-11-17 14:30:45.810321+00	2025-12-17 14:30:46.006538+00	\N	web
200	9	4	42ed04865325931541b1ead6cc45b52c9c93ac860f131517da30a06ed5e1c234	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 17:57:43.31227+00	2025-11-14 17:57:43.594381+00	2025-12-14 17:57:43.535729+00	\N	web
136	9	4	4ef55d9e9c6c9ccc85d9153d8bffbb7cfde7ef29ef1bd9885a2dfd036c3d92f4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:27:24.816114+00	2025-11-14 03:27:26.345965+00	2025-12-14 03:27:25.019358+00	\N	web
137	9	4	00ef35542b47b32f5f9f527c8c6a23986af5a0c46d8d977f8532cc88bf2a0e23	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:27:32.184038+00	2025-11-14 03:27:32.608209+00	2025-12-14 03:27:32.386276+00	\N	web
67	11	8	9a7519b97d5b3467948edb4602e997d6d97de79a16ac4f2791f69b7e5de8fbdf	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 08:42:15.258195+00	2025-11-13 08:42:15.258195+00	2025-12-13 08:42:15.458225+00	\N	web
68	9	4	2b8bdb6c30226f0aa90e881c90e53d0e776c99bdee8c61eb006ecf3aa7ee7920	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 08:50:11.854004+00	2025-11-13 08:50:11.854004+00	2025-12-13 08:50:12.048497+00	\N	web
69	9	4	39e0a0e4f5800e5692ad199ab624c2a37ac62f7cbc9ae1d04c54b11c64d17715	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 08:53:09.660283+00	2025-11-13 08:53:09.660283+00	2025-12-13 08:53:09.85669+00	\N	web
70	9	4	0d6f283eaad481dd4a5c01418e0728b59109ca64f83eabf45cbdf03145424c7a	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:01:29.404458+00	2025-11-13 09:01:29.404458+00	2025-12-13 09:01:29.599244+00	\N	web
118	9	4	19c9890ac877a8fe2f522578a95bd9cdcf215859ef50446e7324a855c2a6fc74	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:21:08.529403+00	2025-11-14 03:21:08.529403+00	2025-12-14 03:21:08.733494+00	\N	web
120	9	4	10c1200818938b2ab8f186834fa250a7fc046b67d20c29d11cb29dc37e0ef8d6	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:21:59.512733+00	2025-11-14 03:21:59.512733+00	2025-12-14 03:21:59.713146+00	\N	web
121	9	4	e6336cb83c73c31566a72c893556493c250c95757bfe66a33395ffa29d38c37b	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:22:05.423037+00	2025-11-14 03:22:05.423037+00	2025-12-14 03:22:05.627589+00	\N	web
142	9	4	1cd83eb2b7925e10a1ed0344a0f351fe20ec4b7a691a69d909a5bc12734dc64f	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:37:36.101648+00	2025-11-14 03:37:36.101648+00	2025-12-14 03:37:36.327489+00	\N	web
126	9	4	0d60f7d71a296534eaa3db85ac8cdc8df3d80f185a2f0b49a5c398ac73b15a46	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:22:51.036081+00	2025-11-14 03:22:51.036081+00	2025-12-14 03:22:51.237477+00	\N	web
156	24	\N	b7ca6dac8fbd24eb6b54532ad39a62152f6c94837de75029a9ca41b1d168c607	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:38:46.389047+00	2025-11-14 05:38:46.389047+00	2025-12-14 05:38:46.590573+00	\N	web
157	24	\N	a46023368c9c67d4cda688578f286e1cff22095ca75615611cbe7835d174ee97	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:38:52.072785+00	2025-11-14 05:38:52.072785+00	2025-12-14 05:38:52.274799+00	\N	web
170	9	4	83a01c393bb1bfa9e9838fa3ba440c6b56c3e68b845fe17ecac73b87e6ab8164	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:02:09.048336+00	2025-11-14 06:02:09.048336+00	2025-12-14 06:02:09.269614+00	\N	web
186	9	4	501a59eb1d01624a07190faf6e124335428843dc39af5f894d6f295f5983efd4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:05:19.152989+00	2025-11-14 07:05:19.152989+00	2025-12-14 07:05:19.376012+00	\N	web
187	24	\N	8728031a6412723d14cec2b2ae692f570fb872698827bbf3f08cad828f9c56fc	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:05:20.102477+00	2025-11-14 07:05:20.102477+00	2025-12-14 07:05:20.304351+00	\N	web
188	30	20	4f2144c7b5306a3b26053afc042a30fd698bc7b3ac8aa71d497a645b2f310f1d	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:05:20.317616+00	2025-11-14 07:05:20.317616+00	2025-12-14 07:05:20.518986+00	\N	web
189	31	20	ceca0a8977c5afc991281bf00b03199d8fc140e0be4aaf500095498b13c7c648	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:05:20.532823+00	2025-11-14 07:05:20.532823+00	2025-12-14 07:05:20.744414+00	\N	web
190	9	4	d1b7d262f877d2fc494fa43c01823db9d27d689e94bca9c48aa7ff12cc4ae62d	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 07:08:51.357322+00	2025-11-14 07:08:51.357322+00	2025-12-14 07:08:51.560239+00	\N	web
220	9	4	088b55bdf2544e9c31cac6b7ebdb0670056091f2e44202029d237852e5171d7b	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 06:29:10.804181+00	2025-11-17 06:29:10.804181+00	2025-12-17 06:29:11.0272+00	\N	web
127	9	4	eb5abb81ab4a6e4ada143e002f7a812baa485fd58e2fc034a81515342ed195a5	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:23:04.440048+00	2025-11-14 03:23:04.830475+00	2025-12-14 03:23:04.638386+00	\N	web
221	9	4	e449af360181c25542f8b7629b47c4125aa22bbc828af61afe8fe692c3431d7e	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 06:29:29.89163+00	2025-11-17 06:29:29.89163+00	2025-12-17 06:29:30.091475+00	\N	web
191	30	20	e47b23268576ccb8296453e3dd43ee7f39e5aa77ac0ba6ef4e8387a6d578e0c3	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:09:54.071831+00	2025-11-14 07:09:54.306432+00	2025-12-14 07:09:54.275544+00	\N	web
227	9	4	2fe00a553a903ca89ae7a2bb8656ee94a25fa03d02c961875a3f379f323790bd	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-18 01:03:39.582427+00	2025-11-18 01:09:01.55375+00	2025-12-18 01:03:39.800455+00	\N	web
73	9	4	5228bc989110061e0e81a2637fe337f3e1938a1aae243c51273ba4a4cdaffecc	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:31:50.129962+00	2025-11-13 09:31:50.129962+00	2025-12-13 09:31:50.330465+00	\N	web
76	9	4	dc7a1a264f7c97b2e39bb2cbda773b470784cc4d164612f0e433c0757424e7a4	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:37:15.719337+00	2025-11-13 09:37:15.719337+00	2025-12-13 09:37:15.943164+00	\N	web
77	9	4	5a53a4525be5803333cde8d7f3797e5a01d064e93ec20efe738405b563976df2	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 09:40:38.794651+00	2025-11-13 09:40:38.794651+00	2025-12-13 09:40:38.994528+00	\N	web
78	9	4	12edd556c332dd523465b35ec534331d9562029eba58c798aa601060054678bf	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 09:40:44.692065+00	2025-11-13 09:40:44.692065+00	2025-12-13 09:40:44.890358+00	\N	web
79	9	4	03123577d38e4b4ed4bf4a79c47576ec7f6f1f6c58264ea3db779a45818a07df	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 09:40:52.181865+00	2025-11-13 09:40:52.181865+00	2025-12-13 09:40:52.381791+00	\N	web
80	9	4	8ae3fbd06ad5c623e4a0214d79f6e6913caeb7bf47d8ea15d21cc9a06f7bb59a	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 09:44:40.888135+00	2025-11-13 09:44:40.888135+00	2025-12-13 09:44:41.106259+00	\N	web
81	9	4	aa70ade7b162b8234773e186fb7004a6b30882eb6543808a657e31e6b46de1e6	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 10:16:10.766039+00	2025-11-13 10:16:10.766039+00	2025-12-13 10:16:10.979196+00	\N	web
82	9	4	a2d2ba25be6cc7e6a66dd85bf0d849932b89137924c6f2626ac7c0dec7e4998a	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 10:32:41.362534+00	2025-11-13 10:32:41.362534+00	2025-12-13 10:32:41.557216+00	\N	web
83	9	4	fcd481567f088c0d111f6ed7da0cb5cd0f10907345001f6922c8544fa853de77	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 10:43:31.675564+00	2025-11-13 10:43:31.675564+00	2025-12-13 10:43:31.897896+00	\N	web
84	9	4	a2baf888c3a14ce0787f0937d32bf0e62e72ea47a0ab819effd81d45e1435470	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 11:52:21.986942+00	2025-11-13 11:52:21.986942+00	2025-12-13 11:52:22.205944+00	\N	web
85	9	4	7fa3f29175680dabbbd006fb4c80f98512b5fe548c841283337c77014e7674df	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 12:12:57.227844+00	2025-11-13 12:12:57.227844+00	2025-12-13 12:12:57.424049+00	\N	web
86	9	4	dfaafd8166d64266993363709be4a4bb9749d54ca2730f58a223a400ba11bd5c	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:14:51.725142+00	2025-11-13 12:14:51.725142+00	2025-12-13 12:14:51.91992+00	\N	web
87	9	4	d4853cfedeb2670e1149627be844c592eb8d61cbefea341c0b2725308c30bf2e	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 12:15:14.369476+00	2025-11-13 12:15:14.369476+00	2025-12-13 12:15:14.566424+00	\N	web
88	9	4	f563805411f25024e5e498d7c6cb76533b6f222de062a4b2efe874be1829d89b	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:20:26.492012+00	2025-11-13 12:20:26.492012+00	2025-12-13 12:20:26.710971+00	\N	web
89	9	4	a4d3190b1defceef3623b7fe252ad45cba2b1469694f1da5b626ab0f40c46533	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:25:31.148698+00	2025-11-13 12:25:31.148698+00	2025-12-13 12:25:31.344828+00	\N	web
90	14	13	d5c5b1934b4596bd965ac599d974851070f001f85b87f12fea378af48a7687cd	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:25:31.577325+00	2025-11-13 12:25:31.577325+00	2025-12-13 12:25:31.776526+00	\N	web
91	15	14	dee51dd8a6649d07d4762ec2ca3543ac85d632ea8460eda4b9e0b555028aacec	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:25:32.011469+00	2025-11-13 12:25:32.011469+00	2025-12-13 12:25:32.208177+00	\N	web
92	16	15	7be60c9ad9f04751980a55899522f61d23e4c7774e017909f01140dcff09c6c7	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:25:32.43485+00	2025-11-13 12:25:32.43485+00	2025-12-13 12:25:32.632695+00	\N	web
93	17	16	7ef50ced3d44fcd0d46a78c5d707174cfe97156317b946a3a2d46a982137cd5c	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 12:27:56.125469+00	2025-11-13 12:27:56.125469+00	2025-12-13 12:27:56.345819+00	\N	web
95	9	4	7e99f668ec0c71cf741663db8ce5a85d1552c22bf74bfdface1ff797b09ea9a6	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 12:30:30.906947+00	2025-11-13 12:30:30.906947+00	2025-12-13 12:30:31.109005+00	\N	web
96	9	4	2b280404c9a94b0d022506228f51005c3a0206d019b818133cfeb6677a0ec123	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 12:35:44.472865+00	2025-11-13 12:35:44.472865+00	2025-12-13 12:35:44.674408+00	\N	web
97	20	15	97dfc25410335a29946fc63ecbd0a42194a68a2806d1829b619099695c3fb46c	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 12:36:35.775355+00	2025-11-13 12:36:35.775355+00	2025-12-13 12:36:35.972086+00	\N	web
98	9	4	af68bc323da8bb7c9f43e87809cbd33a3f0b527042b9bd779f77d6a5540e6783	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 14:50:55.403816+00	2025-11-13 14:50:55.403816+00	2025-12-13 14:50:55.62614+00	\N	web
99	9	4	097dd6447595071526c97b7a46062f9ad2fc539a06186a313b22ca4bcb72e9a9	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 14:51:38.11385+00	2025-11-13 14:51:38.11385+00	2025-12-13 14:51:38.310685+00	\N	web
100	9	4	fecbd59e7b44234db1e34a35624d35dc340caf73d56da3c65e244afee98251c8	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 15:49:04.572469+00	2025-11-13 15:49:04.572469+00	2025-12-13 15:49:04.841623+00	\N	web
101	9	4	de1cbc6cd6275e9023e1718ba40b93e371d3941fcb13b9152c9c59b87341e9a9	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 15:49:39.199375+00	2025-11-13 15:49:39.199375+00	2025-12-13 15:49:39.402488+00	\N	web
102	9	4	ba1c6525bec6df38bd4cc882bf1d207a2591350d1f4cabe8a0d35f6c41254a54	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-13 15:52:52.897364+00	2025-11-13 15:52:52.897364+00	2025-12-13 15:52:53.095353+00	\N	web
103	9	4	0e2c309024591b13df093a23e36edcc7e4ba451b6bea2830e0c1c33b8ca8dadc	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 16:10:30.460818+00	2025-11-13 16:10:30.460818+00	2025-12-13 16:10:30.678825+00	\N	web
104	9	4	8b5333ec221ee5ec4f1222a5e191fe649e24813154fde7012201c405e107e7af	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-13 16:10:35.316215+00	2025-11-13 16:10:35.316215+00	2025-12-13 16:10:35.51636+00	\N	web
105	9	4	7becf12e31ea0365733785e025b4615029c2783e8a4ca9a0cdded3ff846aec9b	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-13 23:52:11.350404+00	2025-11-13 23:52:11.350404+00	2025-12-13 23:52:11.568234+00	\N	web
158	9	4	de67672b885aa2c9eb0e7bbddba22c9966abc34b299c6da1618c6f5ecf61fa82	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:41:36.781721+00	2025-11-14 05:41:36.781721+00	2025-12-14 05:41:37.003778+00	\N	web
107	9	4	1393056c2a57684e43e36c51d7cac0f588d3bae21ea8ac7bd57aa3cec4152018	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 01:15:31.569475+00	2025-11-14 01:15:31.569475+00	2025-12-14 01:15:31.791964+00	2025-11-14 01:16:19.237963+00	web
143	9	4	8a6bebf9cc9d2964c0d1b00f3052ef67da45d35e74c50e6cb1d5ddc5d8eea524	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:39:01.433433+00	2025-11-14 03:39:01.849276+00	2025-12-14 03:39:01.656295+00	\N	web
109	9	4	d0152ef6f9ba6ae49669853c2cadc78828fb7d1bce25f9d1bba335ddf923d233	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 01:37:00.417764+00	2025-11-14 01:37:00.417764+00	2025-12-14 01:37:00.640962+00	\N	web
119	22	4	454985a58a252bd37b41179e22446cc4b5d9d6e3fc048d7e0a671a945b2cc990	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:21:14.068843+00	2025-11-14 03:21:17.553822+00	2025-12-14 03:21:14.267673+00	2025-11-14 03:21:17.5603+00	web
122	9	4	f6cebc68f36c288bd2a69752ab07a8321c4e62d958c86c7b18d1a2c480ed259d	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:22:10.299728+00	2025-11-14 03:22:10.299728+00	2025-12-14 03:22:10.502414+00	\N	web
124	9	4	1d96ba6c0af5db6cf94a1ff06c67a1aff88da585abe36e47d18f3f30a9434a14	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-14 03:22:11.820127+00	2025-11-14 03:22:11.820127+00	2025-12-14 03:22:12.029083+00	\N	web
125	9	4	2724023e01031d43641f19439d477e6f7ef8b0f38e9c38969d527046f18aa166	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 03:22:44.057775+00	2025-11-14 03:22:44.057775+00	2025-12-14 03:22:44.263472+00	\N	web
159	9	4	0947ea06b243a0139a48ff563162b65a4d156ff7403bd71f3511535a9b445044	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:42:03.586213+00	2025-11-14 05:42:03.586213+00	2025-12-14 05:42:03.793033+00	\N	web
160	25	5	74ffecaf44fff953adae60aad02130949ee19eb60c791ea5488be3a6452b1741	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:42:04.036854+00	2025-11-14 05:42:04.036854+00	2025-12-14 05:42:04.237409+00	\N	web
222	9	4	fceb88939c27e79c01a01c3d2287b0d3a37d5472510f12a924569babcfbdd25f	\N	192.168.5.172	curl/8.5.0	{"platform": "unknown", "user_agent": "curl/8.5.0"}	2025-11-17 06:38:32.202736+00	2025-11-17 06:38:32.91379+00	2025-12-17 06:38:32.401212+00	\N	web
163	26	5	4117f1c39a4e8da98ead2e5519a1b998e5bcf5a4e80abb5671af403a5ddf1a9f	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 05:55:06.04391+00	2025-11-14 05:55:06.04391+00	2025-12-14 05:55:06.244544+00	2025-11-14 05:55:06.470386+00	web
108	9	4	3be5bb7dae5883853d4992ba2dc5de11e13976250b9f3e0a2804db81e014e409	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 01:16:21.434672+00	2025-11-14 01:45:13.148782+00	2025-12-14 01:16:21.631242+00	\N	web
171	28	5	b5ee955d0e852ff19b3546d4ea91f1e6ea91d2f34d0bc9b6773f73e62fcd5a16	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:02:09.52167+00	2025-11-14 06:02:09.52167+00	2025-12-14 06:02:09.720232+00	2025-11-14 06:02:09.95762+00	web
161	9	4	5483e154bff78603f2bb6327e302b71b0c099d15cddce261c649a974f81df025	\N	172.18.0.4	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36	{"platform": "Windows", "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}	2025-11-14 05:54:52.698956+00	2025-11-14 06:24:50.266463+00	2025-12-14 05:54:52.901535+00	\N	web
192	30	20	670fa63051dc346c0113f61609a358c13eb74c8239135d4076e5149c5e26b3e3	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 07:10:48.623242+00	2025-11-14 07:10:48.887271+00	2025-12-14 07:10:48.844593+00	\N	web
175	9	4	98c1aadb1bfeb6639e7bbd60094076266a946b505d4463ecb2827c6e4806cedf	\N	192.168.5.172	python-requests/2.31.0	{"platform": "unknown", "user_agent": "python-requests/2.31.0"}	2025-11-14 06:12:44.488351+00	2025-11-14 06:12:44.488351+00	2025-12-14 06:12:44.693021+00	\N	web
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.users (id, username, email, password_hash, full_name, organization_id, is_active, created_at, updated_at, role_id) FROM stdin;
21	testuser_1763048978	testuser1763048978@example.com	$2b$12$f168NyH8ZDBPoIrJbZCbxOLEq9lhUThK8qiyjDwsxxvmSqw1VPxla	Test User	4	t	2025-11-13 15:49:39.438029+00	\N	2
22	testuser_1763090468	test_1763090468@example.com	$2b$12$41LxSxYuWi3agHy8mGB9pOu9EMrvkZ8U.Glu/GHrDUEzBnmhpRLJu	Test User	4	t	2025-11-14 03:21:10.781932+00	\N	2
23	bugfix_test_1763098428	bugfix_test_1763098428@test.com	$2b$12$FnTOTRlnM1Bk4bEPu7XXhustTSqhmwU8lDkdF8kKWbZ7qIqvFPMa2	Bug Fix Test User	4	t	2025-11-14 05:33:48.594739+00	\N	4
24	superadmin	superadmin@system.local	$2b$12$KEwdVn2MZ1C1HcTriT60rOtbAa4pR9HN97heIkngVe.Yv4bdC2Fbm	System Super Administrator	\N	t	2025-11-14 05:35:55.066899+00	\N	1
25	p0_16_1763098922	p0_16_1763098922@test.com	$2b$12$EHrDe8bGpNw0QAt31weRBuw18wlccFyGg54Qui2eGCIzbXUjPa8xm	P0-16 Test User	5	t	2025-11-14 05:42:03.807027+00	\N	4
26	p0_16_1763099705	p0_16_1763099705@test.com	$2b$12$fOPb9PL6vlrpqEUQan/ZIO5CzZI1vQY2eJsFkLMxC00auQp9C/vna	P0-16 Test User	5	t	2025-11-14 05:55:05.820178+00	2025-11-14 05:55:06.263138+00	4
4	testuser	testuser-updated@example.com	$2b$12$/MtzpnmWdK6DTvGbGlgr8O28DGeQFk.PZ4VMHzFvBQeE96lc6.E8q	Test User Updated	4	t	2025-11-05 01:00:56.490578+00	2025-11-05 02:35:32.829526+00	4
9	admin	admin@signage.local	$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2	Administrator	4	t	2025-11-05 09:55:18.836988+00	\N	2
20	admin_sched	admin_sched@example.com	$2b$12$0dGQcpUDHNfMpi8OAy3Nw.RVIlg7ZvIgPJL1ZJGbz0V9RwtYO8eBy	Schedule Admin	15	t	2025-11-13 12:36:27.399512+00	\N	2
19	admin_schedule	admin_schedule@example.com	$2b$12$874FjTH/9M3hoF99oqhTB.9Bd1tG5WN1R4tJgAGVqHHgiFMOxj1wa	Schedule Test Admin	15	t	2025-11-13 12:36:10.262281+00	\N	2
18	admin_content_tag_1763036889	admin_content_tag_1763036889@test.com	$2b$12$qnC/458xAF6H0ni30USKOOA9fE0R903Zm5AWZhZaaHxlM3TpRNb7m	Content Tag Test Admin	\N	t	2025-11-13 12:28:12.148928+00	\N	2
17	testadmin_pa	testadmin_pa@example.com	$2b$12$d.27YC3R9oLGdEVAhMaNduC5tnUc/YEQ6Fq10mrWFekXSQEggNNGm	Test Admin org_13	16	t	2025-11-13 12:25:32.646896+00	\N	2
16	testadmin_sc	testadmin_sc@example.com	$2b$12$6V8Wpskui./5anQnwRWuleWmTkoACwcEGaOmphUFSLEb6qILKnds.	Test Admin org_12	15	t	2025-11-13 12:25:32.222615+00	\N	2
15	testadmin_dp	testadmin_dp@example.com	$2b$12$alCvASc2AFmBqzxw2JVGLO1xhw3JQI5vCESXWJN26LLJZ6jqSL7r6	Test Admin org_11	14	t	2025-11-13 12:25:31.792974+00	\N	2
14	testadmin_ct	testadmin_ct@example.com	$2b$12$aC.hjWOBsiaspII0DHUTOu66PMwVh2X5E4xmmBBvJwNgmNOiFlSDy	Test Admin org_10	13	t	2025-11-13 12:25:31.358692+00	\N	2
13	test_debug_user	test_debug@test.com	$2b$12$leqxjtOgOOvHuTl16lVyxet0stfp21VM5Kcm/pgF1FUeFEhC0Y3Im	Test Debug User	\N	t	2025-11-13 12:20:57.485441+00	\N	2
12	admin_content_tag	admin_content_tag@test.com	$2b$12$JwH6dwAAUt0utgWmy26dyOVPw3vyCG.IVkE7.yKcMkKVfQ4R5PUpm	Content Tag Test Admin	\N	t	2025-11-13 12:20:26.875392+00	\N	2
11	hoteluser	hotel@test.com	$2b$12$IaiCUaRAyLJIBP0At.VC4Oh/7kasr35M4IRE5GP0ba18pfEsw7I1q	Hotel Manager	8	t	2025-11-13 01:53:13.796207+00	\N	2
27	p0_16_1763100011	p0_16_1763100011@test.com	$2b$12$9fRoBRYWpHZQRwRY1/PwEe9fFdqt42vUW/hQZow/chGm6lGlX6Hty	P0-16 Test User	5	t	2025-11-14 06:00:11.878006+00	2025-11-14 06:00:12.344895+00	4
28	p0_16_1763100128	p0_16_1763100128@test.com	$2b$12$A04d5SWLZxrg3lgkBHOKr.u8.3dQ.vQpELhvlreMekRKSX9xY9ea.	P0-16 Test User	5	t	2025-11-14 06:02:09.287488+00	2025-11-14 06:02:09.748364+00	4
29	p0_16_1763100763	p0_16_1763100763@test.com	$2b$12$OK/fToo5OVMH96G4do1Kku2/dpfEDPjdSVT6bpnFgjvNbdPlg70sW	P0-16 Test User	5	t	2025-11-14 06:12:44.704275+00	2025-11-14 06:12:45.1541+00	4
30	tenant_admin	tenant_admin@test.com	$2b$12$FHXj4V7NPJVgKcIr2hRl5.OQiKkIC.tQUD0T4lAD2paKDGgme9OG6	Tenant Administrator	20	t	2025-11-14 07:05:19.422225+00	\N	2
31	tenant_manager	tenant_manager@test.com	$2b$12$9dpXdH7IqD0rtE0yc8KA4OsOOZjKZXt9Chf6HuoSG2OgQyQKB6UHy	Tenant Content Manager	20	t	2025-11-14 07:05:19.653471+00	\N	3
32	tenant_viewer	tenant_viewer@test.com	$2b$12$/SVYT7YT7osicEF1Y.nBzeHtCeKqRdWc/EefMNm98oBv563gWhxWi	Tenant Viewer	20	t	2025-11-14 07:05:19.880061+00	\N	4
\.


--
-- Data for Name: widgets; Type: TABLE DATA; Schema: public; Owner: signage_user
--

COPY public.widgets (id, organization_id, name, description, widget_type, config, layout, is_active, created_by_id, created_at, updated_at) FROM stdin;
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 42, true);


--
-- Name: content_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.content_assignments_id_seq', 12, true);


--
-- Name: content_playback_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.content_playback_logs_id_seq', 1, false);


--
-- Name: content_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.content_tags_id_seq', 7, true);


--
-- Name: contents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.contents_id_seq', 17, true);


--
-- Name: device_commands_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_commands_id_seq', 1, false);


--
-- Name: device_connection_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_connection_logs_id_seq', 3, true);


--
-- Name: device_group_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_group_members_id_seq', 1, false);


--
-- Name: device_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_groups_id_seq', 4, true);


--
-- Name: device_health_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_health_metrics_id_seq', 1, false);


--
-- Name: device_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_logs_id_seq', 1, false);


--
-- Name: device_speed_tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_speed_tests_id_seq', 1, false);


--
-- Name: device_tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.device_tags_id_seq', 1, false);


--
-- Name: devices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.devices_id_seq', 7654, true);


--
-- Name: organizations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.organizations_id_seq', 20, true);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: playlist_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.playlist_assignments_id_seq', 1, false);


--
-- Name: playlist_contents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.playlist_contents_id_seq', 5, true);


--
-- Name: playlist_widgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.playlist_widgets_id_seq', 1, false);


--
-- Name: playlists_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.playlists_id_seq', 23, true);


--
-- Name: pms_configurations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.pms_configurations_id_seq', 1, false);


--
-- Name: pms_guests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.pms_guests_id_seq', 1, false);


--
-- Name: pms_rooms_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.pms_rooms_id_seq', 1, false);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.roles_id_seq', 4, true);


--
-- Name: schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.schedules_id_seq', 3, true);


--
-- Name: tags_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.tags_id_seq', 9, true);


--
-- Name: templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.templates_id_seq', 1, true);


--
-- Name: translations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.translations_id_seq', 1, false);


--
-- Name: user_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.user_sessions_id_seq', 227, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.users_id_seq', 32, true);


--
-- Name: widgets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: signage_user
--

SELECT pg_catalog.setval('public.widgets_id_seq', 1, false);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: content_assignments content_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_pkey PRIMARY KEY (id);


--
-- Name: content_playback_logs content_playback_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs
    ADD CONSTRAINT content_playback_logs_pkey PRIMARY KEY (id);


--
-- Name: content_tags content_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_pkey PRIMARY KEY (id);


--
-- Name: contents contents_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_pkey PRIMARY KEY (id);


--
-- Name: contents contents_storage_key_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_storage_key_key UNIQUE (storage_key);


--
-- Name: device_commands device_commands_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_commands
    ADD CONSTRAINT device_commands_pkey PRIMARY KEY (id);


--
-- Name: device_connection_logs device_connection_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_connection_logs
    ADD CONSTRAINT device_connection_logs_pkey PRIMARY KEY (id);


--
-- Name: device_group_members device_group_members_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members
    ADD CONSTRAINT device_group_members_pkey PRIMARY KEY (id);


--
-- Name: device_groups device_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT device_groups_pkey PRIMARY KEY (id);


--
-- Name: device_health_metrics device_health_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_health_metrics
    ADD CONSTRAINT device_health_metrics_pkey PRIMARY KEY (id);


--
-- Name: device_logs device_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_logs
    ADD CONSTRAINT device_logs_pkey PRIMARY KEY (id);


--
-- Name: device_speed_tests device_speed_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_speed_tests
    ADD CONSTRAINT device_speed_tests_pkey PRIMARY KEY (id);


--
-- Name: device_tags device_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT device_tags_pkey PRIMARY KEY (id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_name_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_name_key UNIQUE (name);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_hash_key UNIQUE (token_hash);


--
-- Name: playlist_assignments playlist_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT playlist_assignments_pkey PRIMARY KEY (id);


--
-- Name: playlist_contents playlist_contents_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_contents
    ADD CONSTRAINT playlist_contents_pkey PRIMARY KEY (id);


--
-- Name: playlist_widgets playlist_widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_widgets
    ADD CONSTRAINT playlist_widgets_pkey PRIMARY KEY (id);


--
-- Name: playlist_widgets playlist_widgets_playlist_id_widget_id_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_widgets
    ADD CONSTRAINT playlist_widgets_playlist_id_widget_id_key UNIQUE (playlist_id, widget_id);


--
-- Name: playlists playlists_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_pkey PRIMARY KEY (id);


--
-- Name: pms_configurations pms_configurations_api_key_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations
    ADD CONSTRAINT pms_configurations_api_key_key UNIQUE (api_key);


--
-- Name: pms_configurations pms_configurations_organization_id_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations
    ADD CONSTRAINT pms_configurations_organization_id_key UNIQUE (organization_id);


--
-- Name: pms_configurations pms_configurations_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations
    ADD CONSTRAINT pms_configurations_pkey PRIMARY KEY (id);


--
-- Name: pms_guests pms_guests_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_guests
    ADD CONSTRAINT pms_guests_pkey PRIMARY KEY (id);


--
-- Name: pms_rooms pms_rooms_organization_id_room_number_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_rooms
    ADD CONSTRAINT pms_rooms_organization_id_room_number_key UNIQUE (organization_id, room_number);


--
-- Name: pms_rooms pms_rooms_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_rooms
    ADD CONSTRAINT pms_rooms_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: schedules schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_pkey PRIMARY KEY (id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: templates templates_organization_id_name_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_organization_id_name_key UNIQUE (organization_id, name);


--
-- Name: templates templates_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_pkey PRIMARY KEY (id);


--
-- Name: translations translations_entity_type_entity_id_language_code_field_name_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_entity_type_entity_id_language_code_field_name_key UNIQUE (entity_type, entity_id, language_code, field_name);


--
-- Name: translations translations_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_pkey PRIMARY KEY (id);


--
-- Name: content_tags unique_content_tag; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT unique_content_tag UNIQUE (content_id, tag_id);


--
-- Name: device_group_members unique_device_per_group; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members
    ADD CONSTRAINT unique_device_per_group UNIQUE (device_id, group_id);


--
-- Name: device_tags unique_device_tag; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT unique_device_tag UNIQUE (device_id, tag_id);


--
-- Name: device_groups unique_group_name_per_org; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT unique_group_name_per_org UNIQUE (organization_id, name, deleted_at);


--
-- Name: playlist_contents unique_playlist_content; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_contents
    ADD CONSTRAINT unique_playlist_content UNIQUE (playlist_id, content_id);


--
-- Name: playlist_assignments unique_playlist_device; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT unique_playlist_device UNIQUE (playlist_id, device_id);


--
-- Name: playlists unique_playlist_name_per_org; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT unique_playlist_name_per_org UNIQUE (organization_id, name, deleted_at);


--
-- Name: playlist_assignments unique_playlist_tag; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT unique_playlist_tag UNIQUE (playlist_id, tag_id);


--
-- Name: roles unique_role_name_per_org; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT unique_role_name_per_org UNIQUE (organization_id, name);


--
-- Name: CONSTRAINT unique_role_name_per_org ON roles; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT unique_role_name_per_org ON public.roles IS 'Role names must be unique within organization (system roles share namespace)';


--
-- Name: tags unique_tag_name_per_org; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT unique_tag_name_per_org UNIQUE (organization_id, tag_name);


--
-- Name: CONSTRAINT unique_tag_name_per_org ON tags; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT unique_tag_name_per_org ON public.tags IS 'Tag names must be unique within an organization';


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_refresh_token_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_refresh_token_key UNIQUE (refresh_token);


--
-- Name: user_sessions user_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_token_key UNIQUE (session_token);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: widgets widgets_organization_id_name_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_organization_id_name_key UNIQUE (organization_id, name);


--
-- Name: widgets widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_pkey PRIMARY KEY (id);


--
-- Name: idx_commands_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_commands_device ON public.device_commands USING btree (device_id);


--
-- Name: idx_commands_device_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_commands_device_status ON public.device_commands USING btree (device_id, status);


--
-- Name: idx_commands_expires; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_commands_expires ON public.device_commands USING btree (expires_at);


--
-- Name: idx_commands_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_commands_organization ON public.device_commands USING btree (organization_id);


--
-- Name: idx_commands_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_commands_status ON public.device_commands USING btree (status);


--
-- Name: idx_content_assignments_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_active ON public.content_assignments USING btree (organization_id, expires_at) WHERE (expires_at IS NOT NULL);


--
-- Name: idx_content_assignments_assigned_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_assigned_by ON public.content_assignments USING btree (assigned_by_id);


--
-- Name: idx_content_assignments_both; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_both ON public.content_assignments USING btree (device_id, content_id);


--
-- Name: idx_content_assignments_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_content ON public.content_assignments USING btree (content_id);


--
-- Name: idx_content_assignments_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_device ON public.content_assignments USING btree (device_id);


--
-- Name: idx_content_assignments_expires; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_expires ON public.content_assignments USING btree (expires_at) WHERE (expires_at IS NOT NULL);


--
-- Name: idx_content_assignments_org_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_org_content ON public.content_assignments USING btree (organization_id, content_id);


--
-- Name: idx_content_assignments_org_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_org_device ON public.content_assignments USING btree (organization_id, device_id);


--
-- Name: idx_content_assignments_org_tag; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_org_tag ON public.content_assignments USING btree (organization_id, tag_id);


--
-- Name: idx_content_assignments_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_organization ON public.content_assignments USING btree (organization_id);


--
-- Name: idx_content_assignments_priority; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_priority ON public.content_assignments USING btree (device_id, priority DESC);


--
-- Name: idx_content_assignments_tag; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_tag ON public.content_assignments USING btree (tag_id) WHERE (tag_id IS NOT NULL);


--
-- Name: idx_content_hash_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_hash_org ON public.contents USING btree (file_hash, organization_id);


--
-- Name: idx_content_org_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_org_active ON public.contents USING btree (organization_id, is_active);


--
-- Name: idx_content_org_created; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_org_created ON public.contents USING btree (organization_id, created_at);


--
-- Name: idx_content_org_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_org_type ON public.contents USING btree (organization_id, content_type);


--
-- Name: idx_content_storage_key; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_storage_key ON public.contents USING btree (storage_key);


--
-- Name: idx_content_tags_both; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_tags_both ON public.content_tags USING btree (content_id, tag_id);


--
-- Name: idx_content_tags_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_tags_content ON public.content_tags USING btree (content_id);


--
-- Name: idx_content_tags_tag; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_tags_tag ON public.content_tags USING btree (tag_id);


--
-- Name: idx_contents_org_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_contents_org_active ON public.contents USING btree (organization_id, is_active, created_at DESC) WHERE (deleted_at IS NULL);


--
-- Name: idx_contents_org_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_contents_org_type ON public.contents USING btree (organization_id, content_type, created_at DESC) WHERE (deleted_at IS NULL);


--
-- Name: idx_device_group_members_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_group_members_device ON public.device_group_members USING btree (device_id);


--
-- Name: idx_device_group_members_group; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_group_members_group ON public.device_group_members USING btree (group_id);


--
-- Name: idx_device_groups_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_groups_org ON public.device_groups USING btree (organization_id, deleted_at);


--
-- Name: idx_device_groups_parent; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_groups_parent ON public.device_groups USING btree (parent_group_id) WHERE (parent_group_id IS NOT NULL);


--
-- Name: idx_device_groups_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_groups_type ON public.device_groups USING btree (organization_id, group_type) WHERE (deleted_at IS NULL);


--
-- Name: idx_device_health_cpu; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_health_cpu ON public.device_health_metrics USING btree (cpu_usage DESC) WHERE (cpu_usage > (80)::numeric);


--
-- Name: idx_device_health_device_time; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_health_device_time ON public.device_health_metrics USING btree (device_id, recorded_at DESC);


--
-- Name: idx_device_health_memory; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_health_memory ON public.device_health_metrics USING btree (memory_usage DESC) WHERE (memory_usage > (80)::numeric);


--
-- Name: idx_device_health_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_health_org ON public.device_health_metrics USING btree (organization_id);


--
-- Name: idx_device_health_time; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_health_time ON public.device_health_metrics USING btree (recorded_at DESC);


--
-- Name: idx_device_logs_connection_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_connection_type ON public.device_connection_logs USING btree (connection_type) WHERE (connection_type IS NOT NULL);


--
-- Name: idx_device_logs_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_device ON public.device_connection_logs USING btree (device_id);


--
-- Name: idx_device_logs_device_time; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_device_time ON public.device_connection_logs USING btree (device_id, logged_at DESC);


--
-- Name: idx_device_logs_effective_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_effective_type ON public.device_connection_logs USING btree (effective_type) WHERE (effective_type IS NOT NULL);


--
-- Name: idx_device_logs_http_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_http_status ON public.device_connection_logs USING btree (http_status) WHERE (http_status IS NOT NULL);


--
-- Name: idx_device_logs_test_trigger; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_test_trigger ON public.device_connection_logs USING btree (test_trigger) WHERE (test_trigger IS NOT NULL);


--
-- Name: idx_device_logs_time; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_time ON public.device_connection_logs USING btree (logged_at DESC);


--
-- Name: idx_device_logs_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_type ON public.device_connection_logs USING btree (event_type);


--
-- Name: idx_device_tags_assigned_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_tags_assigned_by ON public.device_tags USING btree (assigned_by_id);


--
-- Name: idx_device_tags_both; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_tags_both ON public.device_tags USING btree (device_id, tag_id);


--
-- Name: idx_device_tags_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_tags_device ON public.device_tags USING btree (device_id);


--
-- Name: idx_device_tags_tag; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_tags_tag ON public.device_tags USING btree (tag_id);


--
-- Name: idx_devices_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_created_by ON public.devices USING btree (created_by_id);


--
-- Name: idx_devices_device_uuid; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_device_uuid ON public.devices USING btree (device_uuid);


--
-- Name: idx_devices_last_seen; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_last_seen ON public.devices USING btree (last_seen_at);


--
-- Name: idx_devices_org_location_name; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_org_location_name ON public.devices USING btree (organization_id, location_type, device_name);


--
-- Name: idx_devices_org_status_seen; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_org_status_seen ON public.devices USING btree (organization_id, status, last_seen_at DESC);


--
-- Name: idx_devices_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_organization ON public.devices USING btree (organization_id);


--
-- Name: idx_devices_room_number; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_room_number ON public.devices USING btree (room_number);


--
-- Name: idx_devices_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_status ON public.devices USING btree (status);


--
-- Name: idx_devices_unique_code; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_unique_code ON public.devices USING btree (unique_code);


--
-- Name: idx_devices_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_updated_by ON public.devices USING btree (updated_by_id);


--
-- Name: idx_logs_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_logs_device ON public.device_logs USING btree (device_id);


--
-- Name: idx_logs_device_level_timestamp; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_logs_device_level_timestamp ON public.device_logs USING btree (device_id, log_level, recorded_at DESC);


--
-- Name: idx_logs_level; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_logs_level ON public.device_logs USING btree (log_level);


--
-- Name: idx_logs_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_logs_organization ON public.device_logs USING btree (organization_id);


--
-- Name: idx_logs_timestamp; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_logs_timestamp ON public.device_logs USING btree (recorded_at DESC);


--
-- Name: idx_mv_org_health_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX idx_mv_org_health_org ON public.mv_organization_health_summary USING btree (organization_id);


--
-- Name: idx_password_reset_tokens_expires; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_password_reset_tokens_expires ON public.password_reset_tokens USING btree (expires_at);


--
-- Name: idx_password_reset_tokens_hash; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_password_reset_tokens_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: idx_password_reset_tokens_user; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_password_reset_tokens_user ON public.password_reset_tokens USING btree (user_id);


--
-- Name: idx_playback_completed; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_completed ON public.content_playback_logs USING btree (content_id, is_completed) WHERE (is_completed = true);


--
-- Name: idx_playback_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_content ON public.content_playback_logs USING btree (content_id, started_at DESC);


--
-- Name: idx_playback_date; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_date ON public.content_playback_logs USING btree (started_at DESC);


--
-- Name: idx_playback_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_device ON public.content_playback_logs USING btree (device_id, started_at DESC);


--
-- Name: idx_playback_logs_content_date; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_logs_content_date ON public.content_playback_logs USING btree (content_id, started_at DESC);


--
-- Name: idx_playback_logs_device_date; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_logs_device_date ON public.content_playback_logs USING btree (device_id, started_at DESC);


--
-- Name: idx_playback_logs_org_date; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_logs_org_date ON public.content_playback_logs USING btree (organization_id, started_at DESC);


--
-- Name: idx_playback_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_organization ON public.content_playback_logs USING btree (organization_id, started_at DESC);


--
-- Name: idx_playback_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playback_playlist ON public.content_playback_logs USING btree (playlist_id, started_at DESC) WHERE (playlist_id IS NOT NULL);


--
-- Name: idx_playlist_assignments_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_assignments_device ON public.playlist_assignments USING btree (device_id);


--
-- Name: idx_playlist_assignments_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_assignments_playlist ON public.playlist_assignments USING btree (playlist_id);


--
-- Name: idx_playlist_assignments_tag; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_assignments_tag ON public.playlist_assignments USING btree (tag_id);


--
-- Name: idx_playlist_contents_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_contents_content ON public.playlist_contents USING btree (content_id);


--
-- Name: idx_playlist_contents_order; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_contents_order ON public.playlist_contents USING btree (playlist_id, order_index);


--
-- Name: idx_playlist_contents_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_contents_playlist ON public.playlist_contents USING btree (playlist_id);


--
-- Name: idx_playlist_widgets_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_widgets_playlist ON public.playlist_widgets USING btree (playlist_id);


--
-- Name: idx_playlist_widgets_widget; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_widgets_widget ON public.playlist_widgets USING btree (widget_id);


--
-- Name: idx_playlists_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_created_by ON public.playlists USING btree (created_by_id);


--
-- Name: idx_playlists_deleted_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_deleted_at ON public.playlists USING btree (deleted_at);


--
-- Name: idx_playlists_is_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_is_active ON public.playlists USING btree (is_active);


--
-- Name: idx_playlists_org_active_created; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_org_active_created ON public.playlists USING btree (organization_id, is_active, created_at DESC) WHERE (deleted_at IS NULL);


--
-- Name: idx_playlists_org_priority_name; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_org_priority_name ON public.playlists USING btree (organization_id, priority DESC, name) WHERE ((deleted_at IS NULL) AND (is_active = true));


--
-- Name: idx_playlists_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_organization ON public.playlists USING btree (organization_id);


--
-- Name: idx_pms_guests_checkin; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_guests_checkin ON public.pms_guests USING btree (checkin_date);


--
-- Name: idx_pms_guests_language; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_guests_language ON public.pms_guests USING btree (language);


--
-- Name: idx_pms_guests_loyalty; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_guests_loyalty ON public.pms_guests USING btree (loyalty_level);


--
-- Name: idx_pms_guests_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_guests_org ON public.pms_guests USING btree (organization_id);


--
-- Name: idx_pms_guests_room; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_guests_room ON public.pms_guests USING btree (room_number);


--
-- Name: idx_pms_rooms_number; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_rooms_number ON public.pms_rooms USING btree (room_number);


--
-- Name: idx_pms_rooms_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_rooms_org ON public.pms_rooms USING btree (organization_id);


--
-- Name: idx_pms_rooms_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_pms_rooms_status ON public.pms_rooms USING btree (status);


--
-- Name: idx_roles_org_name; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_roles_org_name ON public.roles USING btree (organization_id, name);


--
-- Name: idx_roles_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_roles_organization ON public.roles USING btree (organization_id);


--
-- Name: idx_roles_system; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_roles_system ON public.roles USING btree (is_system_role) WHERE (is_system_role = true);


--
-- Name: idx_schedules_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_active ON public.schedules USING btree (is_active);


--
-- Name: idx_schedules_dates; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_dates ON public.schedules USING btree (start_date, end_date);


--
-- Name: idx_schedules_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_org ON public.schedules USING btree (organization_id);


--
-- Name: idx_schedules_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_playlist ON public.schedules USING btree (playlist_id);


--
-- Name: idx_schedules_priority; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_priority ON public.schedules USING btree (priority DESC);


--
-- Name: idx_sessions_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_active ON public.user_sessions USING btree (user_id, created_at DESC) WHERE (revoked_at IS NULL);


--
-- Name: idx_sessions_expires; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_expires ON public.user_sessions USING btree (expires_at) WHERE (revoked_at IS NULL);


--
-- Name: idx_sessions_ip; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_ip ON public.user_sessions USING btree (ip_address);


--
-- Name: idx_sessions_last_activity; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_last_activity ON public.user_sessions USING btree (last_activity_at DESC);


--
-- Name: idx_sessions_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_organization ON public.user_sessions USING btree (organization_id);


--
-- Name: idx_sessions_refresh; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_refresh ON public.user_sessions USING btree (refresh_token) WHERE (refresh_token IS NOT NULL);


--
-- Name: idx_sessions_token; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_token ON public.user_sessions USING btree (session_token);


--
-- Name: idx_sessions_user; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_sessions_user ON public.user_sessions USING btree (user_id);


--
-- Name: idx_speed_device; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_speed_device ON public.device_speed_tests USING btree (device_id);


--
-- Name: idx_speed_device_tested; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_speed_device_tested ON public.device_speed_tests USING btree (device_id, tested_at DESC);


--
-- Name: idx_speed_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_speed_organization ON public.device_speed_tests USING btree (organization_id);


--
-- Name: idx_speed_quality; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_speed_quality ON public.device_speed_tests USING btree (quality);


--
-- Name: idx_speed_tested; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_speed_tested ON public.device_speed_tests USING btree (tested_at DESC);


--
-- Name: idx_tags_org_tagname_lookup; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_tags_org_tagname_lookup ON public.tags USING btree (organization_id, tag_name);


--
-- Name: idx_tags_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_tags_organization ON public.tags USING btree (organization_id);


--
-- Name: idx_templates_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_templates_active ON public.templates USING btree (is_active);


--
-- Name: idx_templates_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_templates_org ON public.templates USING btree (organization_id);


--
-- Name: idx_templates_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_templates_type ON public.templates USING btree (template_type);


--
-- Name: idx_translations_entity; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_translations_entity ON public.translations USING btree (entity_type, entity_id);


--
-- Name: idx_translations_lang; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_translations_lang ON public.translations USING btree (language_code);


--
-- Name: idx_translations_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_translations_org ON public.translations USING btree (organization_id);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_users_role ON public.users USING btree (role_id);


--
-- Name: idx_widgets_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_widgets_active ON public.widgets USING btree (is_active);


--
-- Name: idx_widgets_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_widgets_org ON public.widgets USING btree (organization_id);


--
-- Name: idx_widgets_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_widgets_type ON public.widgets USING btree (widget_type);


--
-- Name: ix_audit_logs_action; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_action ON public.audit_logs USING btree (action);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_id ON public.audit_logs USING btree (id);


--
-- Name: ix_audit_logs_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_organization_id ON public.audit_logs USING btree (organization_id);


--
-- Name: ix_audit_logs_resource_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_resource_id ON public.audit_logs USING btree (resource_id);


--
-- Name: ix_audit_logs_resource_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_resource_type ON public.audit_logs USING btree (resource_type);


--
-- Name: ix_audit_logs_user_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_audit_logs_user_id ON public.audit_logs USING btree (user_id);


--
-- Name: ix_devices_device_uuid; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX ix_devices_device_uuid ON public.devices USING btree (device_uuid);


--
-- Name: ix_devices_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_devices_id ON public.devices USING btree (id);


--
-- Name: ix_devices_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_devices_organization_id ON public.devices USING btree (organization_id);


--
-- Name: ix_devices_room_number; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_devices_room_number ON public.devices USING btree (room_number);


--
-- Name: ix_devices_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_devices_status ON public.devices USING btree (status);


--
-- Name: ix_devices_unique_code; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX ix_devices_unique_code ON public.devices USING btree (unique_code);


--
-- Name: ix_organizations_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_organizations_id ON public.organizations USING btree (id);


--
-- Name: ix_tags_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_tags_id ON public.tags USING btree (id);


--
-- Name: ix_tags_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_tags_organization_id ON public.tags USING btree (organization_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: unique_org_device_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX unique_org_device_content ON public.content_assignments USING btree (organization_id, device_id, content_id) WHERE (device_id IS NOT NULL);


--
-- Name: unique_org_tag_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX unique_org_tag_content ON public.content_assignments USING btree (organization_id, tag_id, content_id) WHERE (tag_id IS NOT NULL);


--
-- Name: pms_configurations pms_configurations_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER pms_configurations_updated_at BEFORE UPDATE ON public.pms_configurations FOR EACH ROW EXECUTE FUNCTION public.update_pms_updated_at();


--
-- Name: pms_guests pms_guests_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER pms_guests_updated_at BEFORE UPDATE ON public.pms_guests FOR EACH ROW EXECUTE FUNCTION public.update_pms_updated_at();


--
-- Name: pms_rooms pms_rooms_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER pms_rooms_updated_at BEFORE UPDATE ON public.pms_rooms FOR EACH ROW EXECUTE FUNCTION public.update_pms_updated_at();


--
-- Name: schedules schedules_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER schedules_updated_at BEFORE UPDATE ON public.schedules FOR EACH ROW EXECUTE FUNCTION public.update_schedules_updated_at();


--
-- Name: templates templates_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER templates_updated_at BEFORE UPDATE ON public.templates FOR EACH ROW EXECUTE FUNCTION public.update_templates_updated_at();


--
-- Name: translations translations_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER translations_updated_at BEFORE UPDATE ON public.translations FOR EACH ROW EXECUTE FUNCTION public.update_translations_updated_at();


--
-- Name: widgets widgets_updated_at; Type: TRIGGER; Schema: public; Owner: signage_user
--

CREATE TRIGGER widgets_updated_at BEFORE UPDATE ON public.widgets FOR EACH ROW EXECUTE FUNCTION public.update_widgets_updated_at();


--
-- Name: audit_logs audit_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: content_assignments content_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_assigned_by_fkey FOREIGN KEY (assigned_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: content_assignments content_assignments_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.contents(id) ON DELETE CASCADE;


--
-- Name: content_assignments content_assignments_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: content_assignments content_assignments_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: content_assignments content_assignments_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_assignments
    ADD CONSTRAINT content_assignments_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: content_playback_logs content_playback_logs_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs
    ADD CONSTRAINT content_playback_logs_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.contents(id) ON DELETE CASCADE;


--
-- Name: content_playback_logs content_playback_logs_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs
    ADD CONSTRAINT content_playback_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: content_playback_logs content_playback_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs
    ADD CONSTRAINT content_playback_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: content_playback_logs content_playback_logs_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_playback_logs
    ADD CONSTRAINT content_playback_logs_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlists(id) ON DELETE SET NULL;


--
-- Name: content_tags content_tags_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.contents(id) ON DELETE CASCADE;


--
-- Name: content_tags content_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: contents contents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: contents contents_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_uploaded_by_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: device_commands device_commands_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_commands
    ADD CONSTRAINT device_commands_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: device_commands device_commands_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_commands
    ADD CONSTRAINT device_commands_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_commands device_commands_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_commands
    ADD CONSTRAINT device_commands_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: device_connection_logs device_connection_logs_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_connection_logs
    ADD CONSTRAINT device_connection_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_group_members device_group_members_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members
    ADD CONSTRAINT device_group_members_added_by_fkey FOREIGN KEY (added_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: device_group_members device_group_members_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members
    ADD CONSTRAINT device_group_members_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_group_members device_group_members_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_group_members
    ADD CONSTRAINT device_group_members_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.device_groups(id) ON DELETE CASCADE;


--
-- Name: device_groups device_groups_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT device_groups_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: device_groups device_groups_default_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT device_groups_default_playlist_id_fkey FOREIGN KEY (default_playlist_id) REFERENCES public.playlists(id) ON DELETE SET NULL;


--
-- Name: device_groups device_groups_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT device_groups_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: device_groups device_groups_parent_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_groups
    ADD CONSTRAINT device_groups_parent_group_id_fkey FOREIGN KEY (parent_group_id) REFERENCES public.device_groups(id) ON DELETE CASCADE;


--
-- Name: device_health_metrics device_health_metrics_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_health_metrics
    ADD CONSTRAINT device_health_metrics_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_health_metrics device_health_metrics_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_health_metrics
    ADD CONSTRAINT device_health_metrics_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: device_logs device_logs_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_logs
    ADD CONSTRAINT device_logs_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_logs device_logs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_logs
    ADD CONSTRAINT device_logs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: device_speed_tests device_speed_tests_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_speed_tests
    ADD CONSTRAINT device_speed_tests_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_speed_tests device_speed_tests_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_speed_tests
    ADD CONSTRAINT device_speed_tests_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: device_tags device_tags_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT device_tags_assigned_by_fkey FOREIGN KEY (assigned_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: device_tags device_tags_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT device_tags_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: device_tags device_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT device_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: devices devices_assigned_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_assigned_playlist_id_fkey FOREIGN KEY (assigned_playlist_id) REFERENCES public.playlists(id) ON DELETE SET NULL;


--
-- Name: devices devices_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: devices devices_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: devices devices_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_updated_by_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: playlist_assignments playlist_assignments_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT playlist_assignments_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: playlist_assignments playlist_assignments_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT playlist_assignments_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlists(id) ON DELETE CASCADE;


--
-- Name: playlist_assignments playlist_assignments_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT playlist_assignments_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: playlist_contents playlist_contents_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_contents
    ADD CONSTRAINT playlist_contents_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.contents(id) ON DELETE CASCADE;


--
-- Name: playlist_contents playlist_contents_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_contents
    ADD CONSTRAINT playlist_contents_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlists(id) ON DELETE CASCADE;


--
-- Name: playlist_widgets playlist_widgets_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_widgets
    ADD CONSTRAINT playlist_widgets_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlists(id) ON DELETE CASCADE;


--
-- Name: playlist_widgets playlist_widgets_widget_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_widgets
    ADD CONSTRAINT playlist_widgets_widget_id_fkey FOREIGN KEY (widget_id) REFERENCES public.widgets(id) ON DELETE CASCADE;


--
-- Name: playlists playlists_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: playlists playlists_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: pms_configurations pms_configurations_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations
    ADD CONSTRAINT pms_configurations_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: pms_configurations pms_configurations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_configurations
    ADD CONSTRAINT pms_configurations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: pms_guests pms_guests_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_guests
    ADD CONSTRAINT pms_guests_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: pms_rooms pms_rooms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.pms_rooms
    ADD CONSTRAINT pms_rooms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: roles roles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: schedules schedules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: schedules schedules_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: schedules schedules_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlists(id) ON DELETE CASCADE;


--
-- Name: tags tags_assigned_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_assigned_playlist_id_fkey FOREIGN KEY (assigned_playlist_id) REFERENCES public.playlists(id) ON DELETE SET NULL;


--
-- Name: tags tags_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: templates templates_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: templates templates_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: translations translations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: CONSTRAINT users_organization_id_fkey ON users; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT users_organization_id_fkey ON public.users IS 'CASCADE delete users when organization is deleted (Fix P0-7)';


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE SET NULL;


--
-- Name: widgets widgets_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: widgets widgets_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: device_group_members; Type: ROW SECURITY; Schema: public; Owner: signage_user
--

ALTER TABLE public.device_group_members ENABLE ROW LEVEL SECURITY;

--
-- Name: device_group_members device_group_members_isolation; Type: POLICY; Schema: public; Owner: signage_user
--

CREATE POLICY device_group_members_isolation ON public.device_group_members USING (((EXISTS ( SELECT 1
   FROM current_setting('app.is_super_admin'::text, true) current_setting(current_setting)
  WHERE ((current_setting('app.is_super_admin'::text, true))::boolean = true))) OR (EXISTS ( SELECT 1
   FROM public.device_groups
  WHERE ((device_groups.id = device_group_members.group_id) AND (device_groups.organization_id = (current_setting('app.current_organization_id'::text, true))::integer))))));


--
-- Name: device_groups; Type: ROW SECURITY; Schema: public; Owner: signage_user
--

ALTER TABLE public.device_groups ENABLE ROW LEVEL SECURITY;

--
-- Name: device_groups device_groups_isolation; Type: POLICY; Schema: public; Owner: signage_user
--

CREATE POLICY device_groups_isolation ON public.device_groups USING (((EXISTS ( SELECT 1
   FROM current_setting('app.is_super_admin'::text, true) current_setting(current_setting)
  WHERE ((current_setting('app.is_super_admin'::text, true))::boolean = true))) OR (organization_id = (current_setting('app.current_organization_id'::text, true))::integer)));


--
-- Name: POLICY device_groups_isolation ON device_groups; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON POLICY device_groups_isolation ON public.device_groups IS 'Multi-tenant isolation for device groups';


--
-- Name: mv_organization_health_summary; Type: MATERIALIZED VIEW DATA; Schema: public; Owner: signage_user
--

REFRESH MATERIALIZED VIEW public.mv_organization_health_summary;


--
-- PostgreSQL database dump complete
--

\unrestrict itLV1kRi1oSNnEyxAeUcFTKQNdCTnp4nTdA9Jb5S83hTIlqliGjGjc7BicgJhKv

