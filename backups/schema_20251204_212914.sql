--
-- PostgreSQL database dump
--

\restrict DsQawj4W4hjcglayOlX636PwP9DtG0P5P4IspV66Sr85NCWK3y9uM1gmR8Yv50v

-- Dumped from database version 15.15
-- Dumped by pg_dump version 15.15

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

CREATE FUNCTION public.check_device_health_alerts(p_device_id integer) RETURNS TABLE(alert_type character varying, alert_level character varying, alert_message text, metric_value numeric, threshold_value numeric, recorded_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_latest RECORD;
BEGIN
    -- Get latest metrics
    SELECT * INTO v_latest
    FROM get_latest_device_health(p_device_id);

    -- If no data, return empty
    IF v_latest IS NULL THEN
        RETURN;
    END IF;

    -- CPU alert
    IF v_latest.cpu_usage IS NOT NULL THEN
        IF v_latest.cpu_usage > 90 THEN
            RETURN QUERY SELECT 'cpu'::VARCHAR, 'critical'::VARCHAR,
                'CPU usage critically high'::TEXT, v_latest.cpu_usage::NUMERIC, 90::NUMERIC, v_latest.recorded_at;
        ELSIF v_latest.cpu_usage > 80 THEN
            RETURN QUERY SELECT 'cpu'::VARCHAR, 'warning'::VARCHAR,
                'CPU usage high'::TEXT, v_latest.cpu_usage::NUMERIC, 80::NUMERIC, v_latest.recorded_at;
        END IF;
    END IF;

    -- Memory alert
    IF v_latest.memory_usage IS NOT NULL THEN
        IF v_latest.memory_usage > 90 THEN
            RETURN QUERY SELECT 'memory'::VARCHAR, 'critical'::VARCHAR,
                'Memory usage critically high'::TEXT, v_latest.memory_usage::NUMERIC, 90::NUMERIC, v_latest.recorded_at;
        ELSIF v_latest.memory_usage > 80 THEN
            RETURN QUERY SELECT 'memory'::VARCHAR, 'warning'::VARCHAR,
                'Memory usage high'::TEXT, v_latest.memory_usage::NUMERIC, 80::NUMERIC, v_latest.recorded_at;
        END IF;
    END IF;

    -- Disk alert
    IF v_latest.disk_usage IS NOT NULL THEN
        IF v_latest.disk_usage > 95 THEN
            RETURN QUERY SELECT 'disk'::VARCHAR, 'critical'::VARCHAR,
                'Disk space critically low'::TEXT, v_latest.disk_usage::NUMERIC, 95::NUMERIC, v_latest.recorded_at;
        ELSIF v_latest.disk_usage > 85 THEN
            RETURN QUERY SELECT 'disk'::VARCHAR, 'warning'::VARCHAR,
                'Disk space low'::TEXT, v_latest.disk_usage::NUMERIC, 85::NUMERIC, v_latest.recorded_at;
        END IF;
    END IF;

    -- Network latency alert (using network_latency_ms)
    IF v_latest.network_latency_ms IS NOT NULL THEN
        IF v_latest.network_latency_ms > 1000 THEN
            RETURN QUERY SELECT 'latency'::VARCHAR, 'critical'::VARCHAR,
                'Network latency critically high'::TEXT, v_latest.network_latency_ms::NUMERIC, 1000::NUMERIC, v_latest.recorded_at;
        ELSIF v_latest.network_latency_ms > 500 THEN
            RETURN QUERY SELECT 'latency'::VARCHAR, 'warning'::VARCHAR,
                'Network latency high'::TEXT, v_latest.network_latency_ms::NUMERIC, 500::NUMERIC, v_latest.recorded_at;
        END IF;
    END IF;

    -- Connection quality alert (using connection_quality)
    IF v_latest.connection_quality IS NOT NULL THEN
        IF v_latest.connection_quality = 'very_poor' THEN
            RETURN QUERY SELECT 'connection'::VARCHAR, 'critical'::VARCHAR,
                'Connection quality very poor'::TEXT, 0::NUMERIC, 0::NUMERIC, v_latest.recorded_at;
        ELSIF v_latest.connection_quality = 'poor' THEN
            RETURN QUERY SELECT 'connection'::VARCHAR, 'warning'::VARCHAR,
                'Connection quality poor'::TEXT, 0::NUMERIC, 0::NUMERIC, v_latest.recorded_at;
        END IF;
    END IF;

    -- Content errors alert
    IF v_latest.content_errors_count IS NOT NULL AND v_latest.content_errors_count > 5 THEN
        RETURN QUERY SELECT 'content_errors'::VARCHAR, 'warning'::VARCHAR,
            'Multiple content errors detected'::TEXT, v_latest.content_errors_count::NUMERIC, 5::NUMERIC, v_latest.recorded_at;
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

CREATE FUNCTION public.get_latest_device_health(p_device_id integer) RETURNS TABLE(id integer, cpu_usage numeric, memory_usage numeric, memory_total_mb integer, memory_used_mb integer, disk_usage numeric, disk_total_gb integer, disk_used_gb integer, network_latency_ms integer, network_download_mbps numeric, network_upload_mbps numeric, connection_quality character varying, display_resolution character varying, display_refresh_rate integer, gpu_usage numeric, player_version character varying, player_uptime_hours integer, content_errors_count integer, last_error_message text, last_error_at timestamp with time zone, overall_status character varying, is_alert_triggered boolean, alert_message text, extra_data jsonb, recorded_at timestamp without time zone)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        h.id,
        h.cpu_usage,
        h.memory_usage,
        h.memory_total_mb,
        h.memory_used_mb,
        h.disk_usage,
        h.disk_total_gb,
        h.disk_used_gb,
        h.network_latency_ms,
        h.network_download_mbps,
        h.network_upload_mbps,
        h.connection_quality,
        h.display_resolution,
        h.display_refresh_rate,
        h.gpu_usage,
        h.player_version,
        h.player_uptime_hours,
        h.content_errors_count,
        h.last_error_message,
        h.last_error_at,
        h.overall_status,
        h.is_alert_triggered,
        h.alert_message,
        h.metadata AS extra_data,
        h.recorded_at
    FROM device_health_metrics h
    WHERE h.device_id = p_device_id
    ORDER BY h.recorded_at DESC
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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    is_muted boolean DEFAULT false NOT NULL
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

COMMENT ON COLUMN public.content_assignments.assigned_by_id IS 'User who made this assignment';


--
-- Name: COLUMN content_assignments.expires_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.expires_at IS 'Optional expiration date for temporary assignments';


--
-- Name: COLUMN content_assignments.organization_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.organization_id IS 'Organization owning this assignment (multi-tenancy)';


--
-- Name: COLUMN content_assignments.created_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.created_at IS 'Record creation timestamp';


--
-- Name: COLUMN content_assignments.updated_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.updated_at IS 'Record last update timestamp';


--
-- Name: COLUMN content_assignments.is_muted; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.content_assignments.is_muted IS 'Mute this content assignment (true = no audio)';


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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expected_duration integer,
    device_info jsonb,
    playback_quality character varying(20),
    error_count integer DEFAULT 0,
    error_details jsonb
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
    updated_by_id integer,
    deleted_by_id integer,
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
-- Name: COLUMN contents.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.contents.updated_by_id IS 'User who last modified this content';


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
    created_at timestamp with time zone DEFAULT now(),
    assigned_by_id integer
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
    CONSTRAINT device_commands_command_type_check CHECK (((command_type)::text = ANY (ARRAY[('reset'::character varying)::text, ('refresh'::character varying)::text, ('reload'::character varying)::text, ('speed_test'::character varying)::text, ('update_content'::character varying)::text, ('reboot'::character varying)::text, ('screenshot'::character varying)::text, ('volume'::character varying)::text, ('brightness'::character varying)::text]))),
    CONSTRAINT device_commands_status_check CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('sent'::character varying)::text, ('executed'::character varying)::text, ('failed'::character varying)::text, ('expired'::character varying)::text])))
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
    error_message text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    connection_type character varying(20),
    effective_type character varying(10),
    rtt_ms integer,
    endpoint character varying(200),
    http_status integer,
    test_trigger character varying(10),
    test_duration_ms integer,
    latency_ms integer,
    download_speed_mbps numeric(10,2),
    upload_speed_mbps numeric(10,2),
    CONSTRAINT check_connection_type CHECK (((connection_type IS NULL) OR ((connection_type)::text = ANY (ARRAY[('wifi'::character varying)::text, ('ethernet'::character varying)::text, ('cellular'::character varying)::text, ('bluetooth'::character varying)::text, ('wimax'::character varying)::text, ('other'::character varying)::text, ('none'::character varying)::text, ('unknown'::character varying)::text])))),
    CONSTRAINT check_effective_type CHECK (((effective_type IS NULL) OR ((effective_type)::text = ANY (ARRAY[('slow-2g'::character varying)::text, ('2g'::character varying)::text, ('3g'::character varying)::text, ('4g'::character varying)::text, ('5g'::character varying)::text, ('unknown'::character varying)::text])))),
    CONSTRAINT check_rtt_ms CHECK (((rtt_ms IS NULL) OR (rtt_ms >= 0))),
    CONSTRAINT check_test_duration_ms CHECK (((test_duration_ms IS NULL) OR (test_duration_ms >= 0))),
    CONSTRAINT check_test_trigger CHECK (((test_trigger IS NULL) OR ((test_trigger)::text = ANY (ARRAY[('auto'::character varying)::text, ('manual'::character varying)::text])))),
    CONSTRAINT device_connection_logs_download_speed_mbps_check CHECK ((download_speed_mbps >= (0)::numeric)),
    CONSTRAINT device_connection_logs_event_type_check CHECK (((event_type)::text = ANY (ARRAY[('network'::character varying)::text, ('server'::character varying)::text, ('speed_test'::character varying)::text]))),
    CONSTRAINT device_connection_logs_latency_ms_check CHECK ((latency_ms >= 0)),
    CONSTRAINT device_connection_logs_upload_speed_mbps_check CHECK ((upload_speed_mbps >= (0)::numeric))
);


ALTER TABLE public.device_connection_logs OWNER TO signage_user;

--
-- Name: TABLE device_connection_logs; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_connection_logs IS 'Device connection event logs (status changes, connects/disconnects).
Not for metrics storage - use device_speed_tests for network metrics.';


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
-- Name: COLUMN device_connection_logs.error_message; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.error_message IS 'Error details if the event indicates a failure';


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
-- Name: COLUMN device_connection_logs.latency_ms; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.latency_ms IS 'Network latency in milliseconds (for server and speed_test events)';


--
-- Name: COLUMN device_connection_logs.download_speed_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.download_speed_mbps IS 'Download speed in Mbps (for speed_test events only)';


--
-- Name: COLUMN device_connection_logs.upload_speed_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_connection_logs.upload_speed_mbps IS 'Upload speed in Mbps (for speed_test events only)';


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
    volume_level integer DEFAULT 75 NOT NULL,
    background_audio_id integer,
    deleted_by_id integer,
    deleted_at timestamp with time zone,
    CONSTRAINT check_devices_screen_height_positive CHECK (((screen_height IS NULL) OR (screen_height > 0))),
    CONSTRAINT check_devices_screen_width_positive CHECK (((screen_width IS NULL) OR (screen_width > 0))),
    CONSTRAINT check_devices_viewport_height_positive CHECK (((viewport_height IS NULL) OR (viewport_height > 0))),
    CONSTRAINT check_devices_viewport_width_positive CHECK (((viewport_width IS NULL) OR (viewport_width > 0))),
    CONSTRAINT devices_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'active'::character varying, 'inactive'::character varying, 'released'::character varying])::text[]))),
    CONSTRAINT devices_volume_level_check CHECK (((volume_level >= 0) AND (volume_level <= 100)))
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

COMMENT ON COLUMN public.devices.status IS 'Device status: pending (new device awaiting activation), active (operational), inactive (not playing content), released (deleted from device list - shows in Unsigned Pool)';


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

COMMENT ON COLUMN public.devices.released_at IS 'Timestamp when device was released/moved to Unsigned Pool';


--
-- Name: COLUMN devices.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.created_by_id IS 'User ID who created this device (FK to users.id)';


--
-- Name: COLUMN devices.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.updated_by_id IS 'User ID who last updated this device (FK to users.id)';


--
-- Name: COLUMN devices.volume_level; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.volume_level IS 'Device volume level (0-100), default 75%';


--
-- Name: COLUMN devices.background_audio_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.devices.background_audio_id IS 'Background audio content to loop continuously (optional)';


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
-- Name: TABLE device_health_metrics; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_health_metrics IS 'System health metrics (CPU, Memory, Disk).
NOTE: network_* columns are DEPRECATED - use device_speed_tests for network metrics.';


--
-- Name: COLUMN device_health_metrics.network_latency_ms; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_health_metrics.network_latency_ms IS 'DEPRECATED: Use device_speed_tests.latency as source of truth for network metrics';


--
-- Name: COLUMN device_health_metrics.network_download_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_health_metrics.network_download_mbps IS 'DEPRECATED: Use device_speed_tests.download_speed as source of truth for network metrics';


--
-- Name: COLUMN device_health_metrics.network_upload_mbps; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.device_health_metrics.network_upload_mbps IS 'DEPRECATED: Use device_speed_tests.upload_speed as source of truth for network metrics';


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
    CONSTRAINT device_logs_log_level_check CHECK (((log_level)::text = ANY (ARRAY[('log'::character varying)::text, ('info'::character varying)::text, ('warn'::character varying)::text, ('error'::character varying)::text, ('debug'::character varying)::text])))
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
    CONSTRAINT device_speed_tests_quality_check CHECK (((quality)::text = ANY (ARRAY[('good'::character varying)::text, ('fair'::character varying)::text, ('poor'::character varying)::text])))
);


ALTER TABLE public.device_speed_tests OWNER TO signage_user;

--
-- Name: TABLE device_speed_tests; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.device_speed_tests IS 'SOURCE OF TRUTH for network performance metrics (latency, download/upload speeds).
Records network speed test results from device players.';


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
-- Name: menu_categories; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_categories (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    menu_type character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    display_order integer NOT NULL,
    icon character varying(50),
    translations jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    menu_id integer,
    subcategories jsonb DEFAULT '[]'::jsonb NOT NULL
);


ALTER TABLE public.menu_categories OWNER TO signage_user;

--
-- Name: COLUMN menu_categories.menu_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_categories.menu_id IS 'Menu this category belongs to (per-menu categories)';


--
-- Name: COLUMN menu_categories.subcategories; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_categories.subcategories IS 'Array of subcategory names for this category, e.g. ["Nasi", "Mie", "Ayam"]';


--
-- Name: menu_categories_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.menu_categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.menu_categories_id_seq OWNER TO signage_user;

--
-- Name: menu_categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.menu_categories_id_seq OWNED BY public.menu_categories.id;


--
-- Name: menu_import_history; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_import_history (
    id integer NOT NULL,
    menu_id integer NOT NULL,
    organization_id integer NOT NULL,
    imported_by_id integer,
    filename character varying(255) NOT NULL,
    file_size integer,
    rows_total integer NOT NULL,
    rows_success integer NOT NULL,
    rows_failed integer NOT NULL,
    errors jsonb,
    imported_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.menu_import_history OWNER TO signage_user;

--
-- Name: menu_import_history_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.menu_import_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.menu_import_history_id_seq OWNER TO signage_user;

--
-- Name: menu_import_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.menu_import_history_id_seq OWNED BY public.menu_import_history.id;


--
-- Name: menu_item_media; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_item_media (
    id integer NOT NULL,
    menu_item_id integer NOT NULL,
    menu_media_id integer NOT NULL,
    display_order integer DEFAULT 0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.menu_item_media OWNER TO signage_user;

--
-- Name: TABLE menu_item_media; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.menu_item_media IS 'Junction table for multiple media per menu item';


--
-- Name: COLUMN menu_item_media.display_order; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_item_media.display_order IS 'Order in media gallery (0 = first)';


--
-- Name: COLUMN menu_item_media.is_primary; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_item_media.is_primary IS 'Primary media shown as main image in item card';


--
-- Name: menu_item_media_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

ALTER TABLE public.menu_item_media ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.menu_item_media_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: menu_items; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_items (
    id integer NOT NULL,
    menu_id integer NOT NULL,
    organization_id integer NOT NULL,
    content_id integer,
    name character varying(255) NOT NULL,
    description text,
    price numeric(12,2),
    currency character varying(3) NOT NULL,
    image_url character varying(500),
    video_url character varying(500),
    category character varying(100),
    subcategory character varying(100),
    tags character varying(200),
    display_order integer NOT NULL,
    is_active boolean NOT NULL,
    is_featured boolean NOT NULL,
    is_available boolean NOT NULL,
    translations jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    menu_media_id integer,
    variant character varying(200)
);


ALTER TABLE public.menu_items OWNER TO signage_user;

--
-- Name: COLUMN menu_items.variant; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_items.variant IS 'Item variations like Hot, Cold, Large, Small (comma-separated)';


--
-- Name: menu_items_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.menu_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.menu_items_id_seq OWNER TO signage_user;

--
-- Name: menu_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.menu_items_id_seq OWNED BY public.menu_items.id;


--
-- Name: menu_media; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_media (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    file_path character varying(500) NOT NULL,
    file_size integer DEFAULT 0 NOT NULL,
    mime_type character varying(100) NOT NULL,
    width integer,
    height integer,
    thumbnail_path character varying(500),
    title character varying(200),
    alt_text character varying(255),
    is_active boolean DEFAULT true NOT NULL,
    uploaded_by_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    deleted_by_id integer,
    file_hash character varying(64),
    variants jsonb,
    content_hash character varying(64),
    processing_status character varying(20) DEFAULT 'pending'::character varying,
    optimized_at timestamp with time zone,
    original_width integer,
    original_height integer,
    is_animated boolean DEFAULT false
);


ALTER TABLE public.menu_media OWNER TO signage_user;

--
-- Name: TABLE menu_media; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.menu_media IS 'Media files specifically for digital menus (separate from content library)';


--
-- Name: COLUMN menu_media.deleted_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.deleted_by_id IS 'User who deleted this media (for audit trail)';


--
-- Name: COLUMN menu_media.file_hash; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.file_hash IS 'SHA-256 hash of file content for deduplication';


--
-- Name: COLUMN menu_media.variants; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.variants IS 'WebP variant URLs: {thumb, small, hd, 4k, original, fallback}';


--
-- Name: COLUMN menu_media.content_hash; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.content_hash IS 'SHA-256 hash for cache invalidation (post-optimization)';


--
-- Name: COLUMN menu_media.processing_status; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.processing_status IS 'Status: pending, processing, completed, failed';


--
-- Name: COLUMN menu_media.optimized_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.optimized_at IS 'When image optimization was completed';


--
-- Name: COLUMN menu_media.original_width; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.original_width IS 'Original image width before processing';


--
-- Name: COLUMN menu_media.original_height; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.original_height IS 'Original image height before processing';


--
-- Name: COLUMN menu_media.is_animated; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menu_media.is_animated IS 'True if animated GIF';


--
-- Name: menu_media_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

ALTER TABLE public.menu_media ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.menu_media_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: menu_views; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menu_views (
    id integer NOT NULL,
    menu_id integer NOT NULL,
    organization_id integer NOT NULL,
    viewer_ip character varying(45),
    user_agent text,
    device_type character varying(20),
    contact_clicked boolean NOT NULL,
    contact_type character varying(20),
    viewed_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.menu_views OWNER TO signage_user;

--
-- Name: menu_views_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.menu_views_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.menu_views_id_seq OWNER TO signage_user;

--
-- Name: menu_views_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.menu_views_id_seq OWNED BY public.menu_views.id;


--
-- Name: menus; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.menus (
    id integer NOT NULL,
    organization_id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    menu_type character varying(50) NOT NULL,
    is_active boolean NOT NULL,
    show_prices boolean NOT NULL,
    display_mode character varying(20) NOT NULL,
    theme_color character varying(7),
    whatsapp_number character varying(20),
    phone_number character varying(20),
    contact_label character varying(100),
    translations jsonb,
    available_days character varying(50),
    available_hours character varying(20),
    public_url_code character varying(12) NOT NULL,
    qr_code_path character varying(500),
    qr_code_generated_at timestamp with time zone,
    created_by_id integer,
    updated_by_id integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    deleted_at timestamp with time zone,
    deleted_by_id integer,
    outlet_extension character varying(50),
    footer_description text,
    primary_color character varying(7) DEFAULT '#ffffff'::character varying,
    secondary_color character varying(7) DEFAULT '#f3f4f6'::character varying,
    tab_name character varying(100),
    CONSTRAINT check_menus_display_mode CHECK (((display_mode)::text = ANY ((ARRAY['grid'::character varying, 'list'::character varying, 'carousel'::character varying, 'minimalist'::character varying])::text[])))
);


ALTER TABLE public.menus OWNER TO signage_user;

--
-- Name: COLUMN menus.display_mode; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.display_mode IS 'Layout mode for public viewer (grid, list, carousel, minimalist)';


--
-- Name: COLUMN menus.outlet_extension; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.outlet_extension IS 'Outlet phone extension number (non-clickable info badge)';


--
-- Name: COLUMN menus.footer_description; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.footer_description IS 'Custom footer description text for player menu';


--
-- Name: COLUMN menus.primary_color; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.primary_color IS 'Primary/background color (60% of UI)';


--
-- Name: COLUMN menus.secondary_color; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.secondary_color IS 'Secondary color for header/categories (30% of UI)';


--
-- Name: COLUMN menus.tab_name; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.menus.tab_name IS 'Custom tab label for portal view. If null, fallback to menu_type label.';


--
-- Name: menus_id_seq; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.menus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.menus_id_seq OWNER TO signage_user;

--
-- Name: menus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.menus_id_seq OWNED BY public.menus.id;


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
    created_by_id integer,
    updated_by_id integer,
    portal_slug character varying(100),
    CONSTRAINT check_organizations_max_devices_positive CHECK ((max_devices > 0)),
    CONSTRAINT check_organizations_max_users_positive CHECK ((max_users > 0))
);


ALTER TABLE public.organizations OWNER TO signage_user;

--
-- Name: COLUMN organizations.pin; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.organizations.pin IS 'Organization PIN/code for access control (optional)';


--
-- Name: COLUMN organizations.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.organizations.created_by_id IS 'User who created this organization';


--
-- Name: COLUMN organizations.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.organizations.updated_by_id IS 'User who last modified this organization';


--
-- Name: COLUMN organizations.portal_slug; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.organizations.portal_slug IS 'URL-friendly slug for public menu portal (format: organization-name-id)';


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
-- Name: password_history; Type: TABLE; Schema: public; Owner: signage_user
--

CREATE TABLE public.password_history (
    id integer NOT NULL,
    user_id integer NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT '2025-12-04 03:07:22.920628+00'::timestamp with time zone NOT NULL
);


ALTER TABLE public.password_history OWNER TO signage_user;

--
-- Name: password_history_id_seq1; Type: SEQUENCE; Schema: public; Owner: signage_user
--

CREATE SEQUENCE public.password_history_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.password_history_id_seq1 OWNER TO signage_user;

--
-- Name: password_history_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: signage_user
--

ALTER SEQUENCE public.password_history_id_seq1 OWNED BY public.password_history.id;


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
    assigned_by_id integer,
    CONSTRAINT check_assignment_type CHECK ((((device_id IS NOT NULL) AND (tag_id IS NULL)) OR ((device_id IS NULL) AND (tag_id IS NOT NULL))))
);


ALTER TABLE public.playlist_assignments OWNER TO signage_user;

--
-- Name: TABLE playlist_assignments; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON TABLE public.playlist_assignments IS 'Polymorphic assignments: playlist can be assigned to devices OR tags';


--
-- Name: COLUMN playlist_assignments.assigned_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlist_assignments.assigned_by_id IS 'User who made this assignment';


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
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_muted boolean DEFAULT false NOT NULL
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
-- Name: COLUMN playlist_contents.is_muted; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlist_contents.is_muted IS 'Mute this content in playlist (true = no audio)';


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
    background_audio_id integer,
    updated_by_id integer,
    deleted_by_id integer,
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
-- Name: COLUMN playlists.background_audio_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.playlists.background_audio_id IS 'Background audio for this playlist (loops when playlist is active)';


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
    created_by_id integer,
    updated_by_id integer,
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
-- Name: COLUMN roles.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.created_by_id IS 'User who created this role (NULL for system-created roles)';


--
-- Name: COLUMN roles.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.roles.updated_by_id IS 'User who last updated this role (NULL if never updated)';


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
    is_active boolean DEFAULT true,
    created_by_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    device_ids jsonb,
    tag_ids jsonb,
    applies_to_all boolean DEFAULT false,
    updated_by_id integer,
    deleted_by_id integer,
    deleted_at timestamp with time zone,
    mode character varying(20) DEFAULT 'rotate'::character varying,
    color character varying(7) DEFAULT '#3B82F6'::character varying NOT NULL,
    CONSTRAINT check_schedules_date_range CHECK (((end_date IS NULL) OR (end_date >= start_date))),
    CONSTRAINT check_schedules_time_range CHECK (((end_time IS NULL) OR (start_time IS NULL) OR (end_date IS NOT NULL) OR (end_time > start_time))),
    CONSTRAINT schedules_mode_check CHECK (((mode)::text = ANY ((ARRAY['override'::character varying, 'rotate'::character varying])::text[])))
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
-- Name: COLUMN schedules.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.schedules.updated_by_id IS 'User who last updated this schedule (NULL if never updated)';


--
-- Name: COLUMN schedules.mode; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.schedules.mode IS 'Schedule playback mode: override (exclusive) or rotate (join rotation)';


--
-- Name: COLUMN schedules.color; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.schedules.color IS 'Hex color code for calendar display (e.g. #3B82F6)';


--
-- Name: CONSTRAINT check_schedules_date_range ON schedules; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON CONSTRAINT check_schedules_date_range ON public.schedules IS 'Ensures end date is on or after start date';


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
    assigned_playlist_id integer,
    created_by_id integer,
    updated_by_id integer,
    deleted_by_id integer,
    deleted_at timestamp with time zone,
    updated_at timestamp with time zone
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
-- Name: COLUMN tags.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.tags.created_by_id IS 'User who created this tag';


--
-- Name: COLUMN tags.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.tags.updated_by_id IS 'User who last modified this tag';


--
-- Name: COLUMN tags.updated_at; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.tags.updated_at IS 'Timestamp when tag was last updated';


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
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer
);


ALTER TABLE public.templates OWNER TO signage_user;

--
-- Name: COLUMN templates.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.templates.created_by_id IS 'User ID who created this template (FK to users.id)';


--
-- Name: COLUMN templates.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.templates.updated_by_id IS 'User who last updated this template (NULL if never updated)';


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
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by_id integer,
    updated_by_id integer
);


ALTER TABLE public.translations OWNER TO signage_user;

--
-- Name: COLUMN translations.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.translations.created_by_id IS 'User who created this translation';


--
-- Name: COLUMN translations.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.translations.updated_by_id IS 'User who last modified this translation';


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
    CONSTRAINT user_sessions_session_type_check CHECK (((session_type)::text = ANY (ARRAY[('web'::character varying)::text, ('api'::character varying)::text, ('mobile'::character varying)::text, ('device'::character varying)::text])))
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
-- Name: COLUMN users.username; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.users.username IS 'Username unique within organization';


--
-- Name: COLUMN users.email; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.users.email IS 'Email globally unique (for login)';


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
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_by_id integer
);


ALTER TABLE public.widgets OWNER TO signage_user;

--
-- Name: COLUMN widgets.created_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.widgets.created_by_id IS 'User ID who created this widget (FK to users.id)';


--
-- Name: COLUMN widgets.updated_by_id; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON COLUMN public.widgets.updated_by_id IS 'User who last updated this widget (NULL if never updated)';


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
-- Name: menu_categories id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_categories ALTER COLUMN id SET DEFAULT nextval('public.menu_categories_id_seq'::regclass);


--
-- Name: menu_import_history id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_import_history ALTER COLUMN id SET DEFAULT nextval('public.menu_import_history_id_seq'::regclass);


--
-- Name: menu_items id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items ALTER COLUMN id SET DEFAULT nextval('public.menu_items_id_seq'::regclass);


--
-- Name: menu_views id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_views ALTER COLUMN id SET DEFAULT nextval('public.menu_views_id_seq'::regclass);


--
-- Name: menus id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus ALTER COLUMN id SET DEFAULT nextval('public.menus_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: password_history id; Type: DEFAULT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_history ALTER COLUMN id SET DEFAULT nextval('public.password_history_id_seq1'::regclass);


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
-- Name: menu_categories menu_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT menu_categories_pkey PRIMARY KEY (id);


--
-- Name: menu_import_history menu_import_history_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_import_history
    ADD CONSTRAINT menu_import_history_pkey PRIMARY KEY (id);


--
-- Name: menu_item_media menu_item_media_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_item_media
    ADD CONSTRAINT menu_item_media_pkey PRIMARY KEY (id);


--
-- Name: menu_items menu_items_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_pkey PRIMARY KEY (id);


--
-- Name: menu_media menu_media_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_media
    ADD CONSTRAINT menu_media_pkey PRIMARY KEY (id);


--
-- Name: menu_views menu_views_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_views
    ADD CONSTRAINT menu_views_pkey PRIMARY KEY (id);


--
-- Name: menus menus_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus
    ADD CONSTRAINT menus_pkey PRIMARY KEY (id);


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
-- Name: organizations organizations_portal_slug_key; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_portal_slug_key UNIQUE (portal_slug);


--
-- Name: password_history password_history_pkey; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_history
    ADD CONSTRAINT password_history_pkey PRIMARY KEY (id);


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
-- Name: device_tags unique_device_tag; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.device_tags
    ADD CONSTRAINT unique_device_tag UNIQUE (device_id, tag_id);


--
-- Name: menu_categories unique_menu_categories_menu_name; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT unique_menu_categories_menu_name UNIQUE (menu_id, name);


--
-- Name: menu_item_media unique_menu_item_media; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_item_media
    ADD CONSTRAINT unique_menu_item_media UNIQUE (menu_item_id, menu_media_id);


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
-- Name: users users_org_username_unique; Type: CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_org_username_unique UNIQUE (organization_id, username);


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
-- Name: idx_content_assignments_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_organization ON public.content_assignments USING btree (organization_id);


--
-- Name: idx_content_assignments_priority; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_content_assignments_priority ON public.content_assignments USING btree (device_id, priority DESC);


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
-- Name: idx_contents_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_contents_updated_by ON public.contents USING btree (updated_by_id);


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
-- Name: idx_device_logs_download_speed; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_download_speed ON public.device_connection_logs USING btree (download_speed_mbps) WHERE (download_speed_mbps IS NOT NULL);


--
-- Name: idx_device_logs_effective_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_effective_type ON public.device_connection_logs USING btree (effective_type) WHERE (effective_type IS NOT NULL);


--
-- Name: idx_device_logs_http_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_http_status ON public.device_connection_logs USING btree (http_status) WHERE (http_status IS NOT NULL);


--
-- Name: idx_device_logs_latency; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_device_logs_latency ON public.device_connection_logs USING btree (latency_ms) WHERE (latency_ms IS NOT NULL);


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
-- Name: idx_devices_background_audio; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_devices_background_audio ON public.devices USING btree (background_audio_id) WHERE (background_audio_id IS NOT NULL);


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
-- Name: idx_menu_categories_menu; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_categories_menu ON public.menu_categories USING btree (menu_id);


--
-- Name: idx_menu_categories_subcategories; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_categories_subcategories ON public.menu_categories USING gin (subcategories);


--
-- Name: idx_menu_item_media_item; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_item_media_item ON public.menu_item_media USING btree (menu_item_id);


--
-- Name: idx_menu_item_media_media; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_item_media_media ON public.menu_item_media USING btree (menu_media_id);


--
-- Name: idx_menu_item_media_order; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_item_media_order ON public.menu_item_media USING btree (menu_item_id, display_order);


--
-- Name: idx_menu_items_media; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_items_media ON public.menu_items USING btree (menu_media_id);


--
-- Name: idx_menu_media_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_active ON public.menu_media USING btree (is_active) WHERE (deleted_at IS NULL);


--
-- Name: idx_menu_media_content_hash; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_content_hash ON public.menu_media USING btree (content_hash);


--
-- Name: idx_menu_media_deleted; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_deleted ON public.menu_media USING btree (deleted_at);


--
-- Name: idx_menu_media_deleted_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_deleted_by ON public.menu_media USING btree (deleted_by_id);


--
-- Name: idx_menu_media_file_hash; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_file_hash ON public.menu_media USING btree (file_hash) WHERE (file_hash IS NOT NULL);


--
-- Name: idx_menu_media_organization; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_organization ON public.menu_media USING btree (organization_id);


--
-- Name: idx_menu_media_processing_status; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_menu_media_processing_status ON public.menu_media USING btree (processing_status);


--
-- Name: idx_mv_org_health_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX idx_mv_org_health_org ON public.mv_organization_health_summary USING btree (organization_id);


--
-- Name: idx_organizations_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_organizations_created_by ON public.organizations USING btree (created_by_id);


--
-- Name: idx_organizations_portal_slug; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_organizations_portal_slug ON public.organizations USING btree (portal_slug);


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
-- Name: idx_playlist_assignments_assigned_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlist_assignments_assigned_by ON public.playlist_assignments USING btree (assigned_by_id);


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
-- Name: idx_playlists_background_audio; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_playlists_background_audio ON public.playlists USING btree (background_audio_id) WHERE (background_audio_id IS NOT NULL);


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
-- Name: idx_roles_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_roles_created_by ON public.roles USING btree (created_by_id);


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
-- Name: idx_roles_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_roles_updated_by ON public.roles USING btree (updated_by_id);


--
-- Name: idx_schedules_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_active ON public.schedules USING btree (is_active);


--
-- Name: idx_schedules_dates; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_dates ON public.schedules USING btree (start_date, end_date);


--
-- Name: idx_schedules_mode; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_mode ON public.schedules USING btree (mode);


--
-- Name: idx_schedules_org; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_org ON public.schedules USING btree (organization_id);


--
-- Name: idx_schedules_playlist; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_playlist ON public.schedules USING btree (playlist_id);


--
-- Name: idx_schedules_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_schedules_updated_by ON public.schedules USING btree (updated_by_id);


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
-- Name: idx_tags_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_tags_created_by ON public.tags USING btree (created_by_id);


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
-- Name: idx_templates_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_templates_updated_by ON public.templates USING btree (updated_by_id);


--
-- Name: idx_translations_created_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_translations_created_by ON public.translations USING btree (created_by_id);


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
-- Name: idx_users_org_username; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_users_org_username ON public.users USING btree (organization_id, username);


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
-- Name: idx_widgets_updated_by; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX idx_widgets_updated_by ON public.widgets USING btree (updated_by_id);


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
-- Name: ix_menu_categories_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_categories_id ON public.menu_categories USING btree (id);


--
-- Name: ix_menu_categories_menu_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_categories_menu_type ON public.menu_categories USING btree (menu_type);


--
-- Name: ix_menu_categories_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_categories_organization_id ON public.menu_categories USING btree (organization_id);


--
-- Name: ix_menu_import_history_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_import_history_id ON public.menu_import_history USING btree (id);


--
-- Name: ix_menu_import_history_imported_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_import_history_imported_at ON public.menu_import_history USING btree (imported_at);


--
-- Name: ix_menu_import_history_menu_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_import_history_menu_id ON public.menu_import_history USING btree (menu_id);


--
-- Name: ix_menu_import_history_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_import_history_organization_id ON public.menu_import_history USING btree (organization_id);


--
-- Name: ix_menu_items_category; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_category ON public.menu_items USING btree (category);


--
-- Name: ix_menu_items_deleted_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_deleted_at ON public.menu_items USING btree (deleted_at);


--
-- Name: ix_menu_items_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_id ON public.menu_items USING btree (id);


--
-- Name: ix_menu_items_is_featured; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_is_featured ON public.menu_items USING btree (is_featured);


--
-- Name: ix_menu_items_menu_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_menu_id ON public.menu_items USING btree (menu_id);


--
-- Name: ix_menu_items_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_items_organization_id ON public.menu_items USING btree (organization_id);


--
-- Name: ix_menu_views_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_views_id ON public.menu_views USING btree (id);


--
-- Name: ix_menu_views_menu_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_views_menu_id ON public.menu_views USING btree (menu_id);


--
-- Name: ix_menu_views_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_views_organization_id ON public.menu_views USING btree (organization_id);


--
-- Name: ix_menu_views_viewed_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menu_views_viewed_at ON public.menu_views USING btree (viewed_at);


--
-- Name: ix_menus_deleted_at; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menus_deleted_at ON public.menus USING btree (deleted_at);


--
-- Name: ix_menus_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menus_id ON public.menus USING btree (id);


--
-- Name: ix_menus_menu_type; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menus_menu_type ON public.menus USING btree (menu_type);


--
-- Name: ix_menus_organization_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_menus_organization_id ON public.menus USING btree (organization_id);


--
-- Name: ix_menus_public_url_code; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX ix_menus_public_url_code ON public.menus USING btree (public_url_code);


--
-- Name: ix_organizations_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_organizations_id ON public.organizations USING btree (id);


--
-- Name: ix_password_history_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_password_history_id ON public.password_history USING btree (id);


--
-- Name: ix_password_history_user_id; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE INDEX ix_password_history_user_id ON public.password_history USING btree (user_id);


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
-- Name: unique_org_device_content; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX unique_org_device_content ON public.content_assignments USING btree (organization_id, device_id, content_id) WHERE (device_id IS NOT NULL);


--
-- Name: unique_tag_name_per_org_active; Type: INDEX; Schema: public; Owner: signage_user
--

CREATE UNIQUE INDEX unique_tag_name_per_org_active ON public.tags USING btree (organization_id, tag_name) WHERE (deleted_at IS NULL);


--
-- Name: INDEX unique_tag_name_per_org_active; Type: COMMENT; Schema: public; Owner: signage_user
--

COMMENT ON INDEX public.unique_tag_name_per_org_active IS 'Ensures tag names are unique per organization, but only for active (non-deleted) tags';


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
-- Name: content_tags content_tags_assigned_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.content_tags
    ADD CONSTRAINT content_tags_assigned_by_id_fkey FOREIGN KEY (assigned_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: contents contents_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: contents contents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: contents contents_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.contents
    ADD CONSTRAINT contents_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: devices devices_background_audio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_background_audio_id_fkey FOREIGN KEY (background_audio_id) REFERENCES public.contents(id) ON DELETE SET NULL;


--
-- Name: devices devices_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: devices devices_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: menu_categories menu_categories_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT menu_categories_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.menus(id) ON DELETE CASCADE;


--
-- Name: menu_categories menu_categories_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT menu_categories_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menu_import_history menu_import_history_imported_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_import_history
    ADD CONSTRAINT menu_import_history_imported_by_id_fkey FOREIGN KEY (imported_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: menu_import_history menu_import_history_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_import_history
    ADD CONSTRAINT menu_import_history_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.menus(id) ON DELETE CASCADE;


--
-- Name: menu_import_history menu_import_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_import_history
    ADD CONSTRAINT menu_import_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menu_item_media menu_item_media_menu_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_item_media
    ADD CONSTRAINT menu_item_media_menu_item_id_fkey FOREIGN KEY (menu_item_id) REFERENCES public.menu_items(id) ON DELETE CASCADE;


--
-- Name: menu_item_media menu_item_media_menu_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_item_media
    ADD CONSTRAINT menu_item_media_menu_media_id_fkey FOREIGN KEY (menu_media_id) REFERENCES public.menu_media(id) ON DELETE CASCADE;


--
-- Name: menu_items menu_items_content_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_content_id_fkey FOREIGN KEY (content_id) REFERENCES public.contents(id) ON DELETE SET NULL;


--
-- Name: menu_items menu_items_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.menus(id) ON DELETE CASCADE;


--
-- Name: menu_items menu_items_menu_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_menu_media_id_fkey FOREIGN KEY (menu_media_id) REFERENCES public.menu_media(id) ON DELETE SET NULL;


--
-- Name: menu_items menu_items_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menu_media menu_media_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_media
    ADD CONSTRAINT menu_media_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: menu_media menu_media_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_media
    ADD CONSTRAINT menu_media_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menu_media menu_media_uploaded_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_media
    ADD CONSTRAINT menu_media_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: menu_views menu_views_menu_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_views
    ADD CONSTRAINT menu_views_menu_id_fkey FOREIGN KEY (menu_id) REFERENCES public.menus(id) ON DELETE CASCADE;


--
-- Name: menu_views menu_views_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menu_views
    ADD CONSTRAINT menu_views_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menus menus_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus
    ADD CONSTRAINT menus_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: menus menus_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus
    ADD CONSTRAINT menus_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: menus menus_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus
    ADD CONSTRAINT menus_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: menus menus_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.menus
    ADD CONSTRAINT menus_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: organizations organizations_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: organizations organizations_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: password_history password_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_history
    ADD CONSTRAINT password_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: playlist_assignments playlist_assignments_assigned_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlist_assignments
    ADD CONSTRAINT playlist_assignments_assigned_by_id_fkey FOREIGN KEY (assigned_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: playlists playlists_background_audio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_background_audio_id_fkey FOREIGN KEY (background_audio_id) REFERENCES public.contents(id) ON DELETE SET NULL;


--
-- Name: playlists playlists_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: playlists playlists_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: playlists playlists_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: playlists playlists_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.playlists
    ADD CONSTRAINT playlists_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: roles roles_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: roles roles_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: roles roles_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: schedules schedules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_created_by_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);


--
-- Name: schedules schedules_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: schedules schedules_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tags tags_assigned_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_assigned_playlist_id_fkey FOREIGN KEY (assigned_playlist_id) REFERENCES public.playlists(id) ON DELETE SET NULL;


--
-- Name: tags tags_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tags tags_deleted_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_deleted_by_id_fkey FOREIGN KEY (deleted_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: tags tags_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: tags tags_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: templates templates_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: translations translations_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: translations translations_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: translations translations_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.translations
    ADD CONSTRAINT translations_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: widgets widgets_updated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: signage_user
--

ALTER TABLE ONLY public.widgets
    ADD CONSTRAINT widgets_updated_by_id_fkey FOREIGN KEY (updated_by_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict DsQawj4W4hjcglayOlX636PwP9DtG0P5P4IspV66Sr85NCWK3y9uM1gmR8Yv50v

