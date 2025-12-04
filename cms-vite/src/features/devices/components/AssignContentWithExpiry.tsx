/**
 * Assign Content with Expiry Component
 *
 * Features:
 * - Content selector with search
 * - Priority slider (1-10)
 * - Optional schedule JSON input
 * - Expiry date/time picker
 * - Countdown for expiring assignments
 * - Warning for soon-to-expire assignments
 */

import React, { useState, useMemo } from 'react';
import { Search, Loader2, AlertTriangle, Calendar, Clock, Trash2 } from 'lucide-react';
import { formatDistanceToNow, format, addDays, isAfter, isBefore, differenceInDays } from 'date-fns';
import { toast } from '@/shared/utils/toast';
import { useContentList } from '@/features/contents/hooks/useContent';
import {
  useDeviceContents,
  useAssignContent,
  useUnassignContent,
} from '../hooks/useDeviceAssignments';
import type { AssignContentRequest, ContentAssignment } from '../types/assignment';

interface AssignContentWithExpiryProps {
  deviceId: number;
  deviceName?: string;
  onSuccess?: () => void;
}

export const AssignContentWithExpiry: React.FC<AssignContentWithExpiryProps> = ({
  deviceId,
  deviceName,
  onSuccess,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null);
  const [priority, setPriority] = useState(5);
  const [schedule, setSchedule] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [expiryTime, setExpiryTime] = useState('23:59');
  const [showForm, setShowForm] = useState(false);

  // Fetch available content
  const { data: contentData, isLoading: loadingContent } = useContentList({ limit: 1000 });

  // Fetch current assignments
  const { data: assignmentsData, isLoading: loadingAssignments } = useDeviceContents(deviceId);

  const assignContent = useAssignContent();
  const unassignContent = useUnassignContent();

  // Filter available content (exclude already assigned)
  const availableContent = useMemo(() => {
    if (!contentData?.data) return [];

    const assignedIds = new Set(assignmentsData?.items.map((a) => a.content_id) || []);

    return contentData.data.filter((content) => {
      const isAssigned = assignedIds.has(content.id);
      const matchesSearch =
        content.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        content.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        content.content_type.toLowerCase().includes(searchQuery.toLowerCase());

      return !isAssigned && matchesSearch;
    });
  }, [contentData, assignmentsData, searchQuery]);

  // Calculate expiry status for assignments
  const enrichedAssignments = useMemo(() => {
    if (!assignmentsData?.items) return [];

    return assignmentsData.items.map((assignment) => {
      const now = new Date();
      const expiresAt = assignment.expires_at ? new Date(assignment.expires_at) : null;
      const daysUntilExpiry = expiresAt ? differenceInDays(expiresAt, now) : null;

      return {
        ...assignment,
        is_expired: expiresAt ? isBefore(expiresAt, now) : false,
        is_expiring_soon: expiresAt ? daysUntilExpiry !== null && daysUntilExpiry <= 7 && daysUntilExpiry >= 0 : false,
        days_until_expiry: daysUntilExpiry,
      };
    });
  }, [assignmentsData]);

  // Handle assignment
  const handleAssign = async () => {
    if (!selectedContentId) return;

    const data: AssignContentRequest = {
      content_id: selectedContentId,
      priority,
    };

    // Parse schedule if provided
    if (schedule.trim()) {
      try {
        data.schedule = JSON.parse(schedule);
      } catch (err) {
        toast.error('Invalid JSON in schedule field');
        return;
      }
    }

    // Combine date and time for expiry
    if (expiryDate) {
      const expiryDateTime = `${expiryDate}T${expiryTime}:00`;
      data.expires_at = new Date(expiryDateTime).toISOString();
    }

    await assignContent.mutateAsync(
      { deviceId, data },
      {
        onSuccess: () => {
          setSelectedContentId(null);
          setPriority(5);
          setSchedule('');
          setExpiryDate('');
          setExpiryTime('23:59');
          setShowForm(false);
          onSuccess?.();
        },
      }
    );
  };

  // Handle unassignment
  const handleUnassign = async (contentId: number) => {
    await unassignContent.mutateAsync({ deviceId, contentId });
  };

  // Quick expiry presets
  const setQuickExpiry = (days: number) => {
    const targetDate = addDays(new Date(), days);
    setExpiryDate(format(targetDate, 'yyyy-MM-dd'));
  };

  return (
    <div className="space-y-6">
      {/* Current Assignments */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Current Content Assignments</h3>

        {loadingAssignments ? (
          <div className="text-center py-8 text-gray-500">Loading assignments...</div>
        ) : enrichedAssignments.length === 0 ? (
          <div className="text-center py-8 text-gray-500 border rounded-lg">
            No content assigned yet
          </div>
        ) : (
          <div className="space-y-2">
            {enrichedAssignments.map((assignment) => (
              <div
                key={assignment.id}
                className={`p-4 border rounded-lg ${
                  assignment.is_expired
                    ? 'bg-red-50 border-red-200'
                    : assignment.is_expiring_soon
                    ? 'bg-yellow-50 border-yellow-200'
                    : 'bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium">{assignment.content_name}</h4>
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                      <span className="capitalize">{assignment.content_type.replace('_', ' ')}</span>
                      <span>•</span>
                      <span>Priority: {assignment.priority}</span>
                      {assignment.expires_at && (
                        <>
                          <span>•</span>
                          <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {assignment.is_expired ? (
                              <span className="text-red-600 font-medium">Expired</span>
                            ) : assignment.is_expiring_soon ? (
                              <span className="text-yellow-700 font-medium">
                                Expires in {assignment.days_until_expiry} days
                              </span>
                            ) : (
                              <span>
                                Expires {formatDistanceToNow(new Date(assignment.expires_at), { addSuffix: true })}
                              </span>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                    {assignment.expires_at && !assignment.is_expired && (
                      <div className="text-xs text-gray-500 mt-1">
                        {format(new Date(assignment.expires_at), 'PPpp')}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleUnassign(assignment.content_id)}
                    disabled={unassignContent.isPending}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Unassign content"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {assignment.is_expiring_soon && !assignment.is_expired && (
                  <div className="mt-3 flex items-start gap-2 p-2 bg-yellow-100 rounded">
                    <AlertTriangle className="w-4 h-4 text-yellow-700 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-yellow-800">
                      This assignment will expire soon. Consider extending or reassigning.
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assign New Content */}
      <div className="border-t pt-6">
        {!showForm ? (
          <button
            onClick={() => setShowForm(true)}
            className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-blue-500 hover:text-blue-600 transition-colors"
          >
            + Assign New Content
          </button>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Assign New Content</h3>
              <button
                onClick={() => setShowForm(false)}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>

            {/* Content Selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Content
              </label>
              <div className="relative mb-2">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search content..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {loadingContent ? (
                <div className="text-center py-4 text-gray-500">Loading content...</div>
              ) : (
                <div className="border rounded-lg max-h-48 overflow-y-auto">
                  {availableContent.length === 0 ? (
                    <div className="text-center py-4 text-gray-500">
                      No available content found
                    </div>
                  ) : (
                    <div className="divide-y">
                      {availableContent.map((content) => (
                        <label
                          key={content.id}
                          className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                            selectedContentId === content.id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <input
                            type="radio"
                            checked={selectedContentId === content.id}
                            onChange={() => setSelectedContentId(content.id)}
                            className="w-4 h-4 text-blue-600"
                          />
                          <div className="flex-1">
                            <div className="font-medium">{content.title}</div>
                            <div className="text-sm text-gray-500 capitalize">
                              {content.content_type.replace('_', ' ')}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Priority Slider */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority: {priority}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Low (1)</span>
                <span>High (10)</span>
              </div>
            </div>

            {/* Expiry Date/Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expiry Date & Time (Optional)
              </label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={expiryDate}
                  onChange={(e) => setExpiryDate(e.target.value)}
                  min={format(new Date(), 'yyyy-MM-dd')}
                  className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <input
                  type="time"
                  value={expiryTime}
                  onChange={(e) => setExpiryTime(e.target.value)}
                  className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => setQuickExpiry(7)}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                >
                  7 days
                </button>
                <button
                  onClick={() => setQuickExpiry(30)}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                >
                  30 days
                </button>
                <button
                  onClick={() => setQuickExpiry(90)}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                >
                  90 days
                </button>
                <button
                  onClick={() => {
                    setExpiryDate('');
                    setExpiryTime('23:59');
                  }}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                >
                  No expiry
                </button>
              </div>
            </div>

            {/* Schedule JSON (Advanced) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Schedule (Optional JSON)
              </label>
              <textarea
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
                placeholder='{"days": [1,2,3,4,5], "time": "09:00-17:00"}'
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                rows={3}
              />
              <p className="text-xs text-gray-500 mt-1">
                Optional: Specify when content should display (JSON format)
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={assignContent.isPending}
              >
                Cancel
              </button>
              <button
                onClick={handleAssign}
                disabled={!selectedContentId || assignContent.isPending}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {assignContent.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Assign Content
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
