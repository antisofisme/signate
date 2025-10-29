import { useState } from 'react';
import { Search, Copy, Check, ChevronDown, ChevronRight, Info } from 'lucide-react';
import {
  SYSTEM_VARIABLES,
  WEATHER_VARIABLES,
  DEVICE_VARIABLES,
  FIREBIRD_VARIABLES,
  type TemplateVariable,
  type VariableCategory,
} from '../../types/template';

interface VariablePickerProps {
  onVariableSelect: (variable: string) => void;
  className?: string;
}

interface VariableCategoryGroup {
  name: string;
  category: VariableCategory;
  variables: TemplateVariable[];
  icon: string;
  color: string;
}

export default function VariablePicker({ onVariableSelect, className = '' }: VariablePickerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<VariableCategory>>(
    new Set(['system', 'weather', 'device', 'firebird'])
  );
  const [copiedVariable, setCopiedVariable] = useState<string | null>(null);
  const [hoveredVariable, setHoveredVariable] = useState<string | null>(null);

  const categories: VariableCategoryGroup[] = [
    {
      name: 'System Variables',
      category: 'system',
      variables: SYSTEM_VARIABLES,
      icon: '🖥️',
      color: 'blue',
    },
    {
      name: 'Weather Variables',
      category: 'weather',
      variables: WEATHER_VARIABLES,
      icon: '🌤️',
      color: 'sky',
    },
    {
      name: 'Device Variables',
      category: 'device',
      variables: DEVICE_VARIABLES,
      icon: '📱',
      color: 'purple',
    },
    {
      name: 'Firebird Variables',
      category: 'firebird',
      variables: FIREBIRD_VARIABLES,
      icon: '🔥',
      color: 'orange',
    },
  ];

  const toggleCategory = (category: VariableCategory) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const handleVariableClick = (variableName: string) => {
    const variableSyntax = `{{ ${variableName} }}`;
    onVariableSelect(variableSyntax);

    // Copy to clipboard
    navigator.clipboard.writeText(variableSyntax);
    setCopiedVariable(variableName);
    setTimeout(() => setCopiedVariable(null), 2000);
  };

  const filterVariables = (variables: TemplateVariable[]) => {
    if (!searchQuery) return variables;
    const query = searchQuery.toLowerCase();
    return variables.filter(
      (v) =>
        v.name.toLowerCase().includes(query) ||
        v.description.toLowerCase().includes(query)
    );
  };

  const getCategoryColorClass = (color: string) => {
    const colorMap: Record<string, string> = {
      blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      sky: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400',
      purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    };
    return colorMap[color] || colorMap.blue;
  };

  return (
    <div className={`flex flex-col h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Template Variables
        </h3>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search variables..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:text-white"
          />
        </div>
      </div>

      {/* Variable Categories */}
      <div className="flex-1 overflow-y-auto">
        {categories.map((category) => {
          const filteredVars = filterVariables(category.variables);
          if (searchQuery && filteredVars.length === 0) return null;

          const isExpanded = expandedCategories.has(category.category);

          return (
            <div key={category.category} className="border-b border-gray-200 dark:border-gray-700">
              {/* Category Header */}
              <button
                onClick={() => toggleCategory(category.category)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{category.icon}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {category.name}
                  </span>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${getCategoryColorClass(category.color)}`}>
                    {filteredVars.length}
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {/* Variables List */}
              {isExpanded && (
                <div className="bg-gray-50 dark:bg-gray-900/50">
                  {filteredVars.map((variable) => (
                    <div
                      key={variable.name}
                      className="relative"
                      onMouseEnter={() => setHoveredVariable(variable.name)}
                      onMouseLeave={() => setHoveredVariable(null)}
                    >
                      <button
                        onClick={() => handleVariableClick(variable.name)}
                        className="w-full px-4 py-2.5 text-left hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <code className="text-xs font-mono text-gray-900 dark:text-white font-medium">
                                {variable.name}
                              </code>
                              {copiedVariable === variable.name ? (
                                <Check className="w-3 h-3 text-green-500 flex-shrink-0" />
                              ) : (
                                <Copy className="w-3 h-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                              )}
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                              {variable.description}
                            </p>
                          </div>
                        </div>
                      </button>

                      {/* Tooltip */}
                      {hoveredVariable === variable.name && variable.example && (
                        <div className="absolute left-full top-0 ml-2 z-50 w-64 p-3 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg shadow-xl border border-gray-700 dark:border-gray-600">
                          <div className="flex items-start gap-2 mb-2">
                            <Info className="w-3 h-3 text-blue-400 flex-shrink-0 mt-0.5" />
                            <div>
                              <div className="font-semibold mb-1">Example Usage:</div>
                              <code className="block p-2 bg-gray-800 dark:bg-gray-800 rounded text-green-400 break-all">
                                {variable.example}
                              </code>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Help */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
        <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
          <p className="font-medium">💡 Quick Tips:</p>
          <ul className="list-disc list-inside space-y-0.5 ml-1">
            <li>Click to insert variable</li>
            <li>Hover for examples</li>
            <li>Use {'{{ }}'} for output</li>
            <li>Use {'{% %}'} for logic</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
