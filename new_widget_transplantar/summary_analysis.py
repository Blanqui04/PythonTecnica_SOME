# src/gui/windows/components/summary_analysis.py
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from src.models.dimensional.dimensional_result import DimensionalResult


class SummaryAnalyzer:
    """Advanced analysis engine for dimensional summary data"""
    
    def __init__(self):
        self.analysis_cache = {}
        self.historical_data = []
        
    def analyze_quality_metrics(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Comprehensive quality analysis"""
        if not results:
            return self._empty_quality_metrics()
            
        analysis = {
            'overall_quality': self._calculate_overall_quality(results),
            'quality_distribution': self._analyze_quality_distribution(results),
            'critical_issues': self._identify_critical_issues(results),
            'quality_trends': self._analyze_quality_trends(results),
            'recommendations': self._generate_quality_recommendations(results)
        }
        
        return analysis
    
    def analyze_performance_metrics(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance and efficiency metrics"""
        analysis = {
            'efficiency_score': self._calculate_efficiency_score(session_data),
            'throughput_metrics': self._analyze_throughput(session_data),
            'resource_utilization': self._analyze_resource_usage(session_data),
            'optimization_opportunities': self._identify_optimization_opportunities(session_data)
        }
        
        return analysis
    
    def analyze_data_integrity(self, table_data: pd.DataFrame, original_data: Dict) -> Dict[str, Any]:
        """Comprehensive data integrity analysis"""
        if table_data is None or table_data.empty:
            return self._empty_integrity_metrics()
            
        analysis = {
            'completeness_analysis': self._analyze_completeness(table_data),
            'consistency_analysis': self._analyze_consistency(table_data),
            'accuracy_analysis': self._analyze_accuracy(table_data, original_data),
            'data_quality_score': 0.0,
            'integrity_issues': [],
            'improvement_suggestions': []
        }
        
        # Calculate overall data quality score
        analysis['data_quality_score'] = self._calculate_data_quality_score(analysis)
        
        return analysis
    
    def generate_intelligent_recommendations(self, 
                                           quality_data: Dict[str, Any],
                                           performance_data: Dict[str, Any],
                                           integrity_data: Dict[str, Any]) -> List[str]:
        """Generate intelligent, actionable recommendations"""
        recommendations = []
        
        # Quality-based recommendations
        quality_score = quality_data.get('overall_quality', {}).get('score', 0)
        if quality_score < 95:
            if quality_score < 80:
                recommendations.append("🚨 CRITICAL: Quality score below 80% - Immediate process review required")
            else:
                recommendations.append("⚠️ Quality improvement needed - Focus on failed dimensions analysis")
        
        # Performance-based recommendations
        efficiency = performance_data.get('efficiency_score', 0)
        if efficiency < 85:
            recommendations.append("⚡ Performance optimization needed - Review processing bottlenecks")
        
        # Data integrity recommendations
        completeness = integrity_data.get('completeness_analysis', {}).get('overall_score', 0)
        if completeness < 90:
            recommendations.append("📊 Increase measurement coverage for better statistical confidence")
        
        # Advanced pattern-based recommendations
        recommendations.extend(self._generate_pattern_based_recommendations(
            quality_data, performance_data, integrity_data
        ))
        
        return recommendations[:8]  # Limit to most important recommendations
    
    def _calculate_overall_quality(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Calculate comprehensive quality metrics"""
        if not results:
            return {'score': 0.0, 'grade': 'N/A', 'status': 'No Data'}
        
        total = len(results)
        passed = sum(1 for r in results if self._get_status(r) == 'GOOD')
        failed = sum(1 for r in results if self._get_status(r) == 'BAD')
        warning = sum(1 for r in results if self._get_status(r) == 'WARNING')
        
        # Base success rate
        success_rate = (passed / total) * 100
        
        # Quality adjustments
        warning_penalty = (warning / total) * 5  # 5% penalty per warning
        critical_penalty = self._calculate_critical_penalty(results)
        
        # Final quality score
        quality_score = max(0, success_rate - warning_penalty - critical_penalty)
        
        # Quality grade
        if quality_score >= 95:
            grade, status = 'A+', 'Excellent'
        elif quality_score >= 90:
            grade, status = 'A', 'Very Good'
        elif quality_score >= 85:
            grade, status = 'B+', 'Good'
        elif quality_score >= 80:
            grade, status = 'B', 'Acceptable'
        elif quality_score >= 70:
            grade, status = 'C', 'Needs Improvement'
        else:
            grade, status = 'F', 'Critical Issues'
        
        return {
            'score': quality_score,
            'grade': grade,
            'status': status,
            'passed': passed,
            'failed': failed,
            'warning': warning,
            'total': total
        }
    
    def _analyze_quality_distribution(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Analyze quality distribution across different dimensions"""
        distribution = {
            'by_cavity': {},
            'by_evaluation_type': {},
            'by_tolerance_range': {},
            'failure_patterns': []
        }
        
        # Cavity analysis
        cavity_stats = {}
        for result in results:
            cavity = getattr(result, 'cavity', 1) or 1
            status = self._get_status(result)
            
            if cavity not in cavity_stats:
                cavity_stats[cavity] = {'total': 0, 'passed': 0, 'failed': 0}
            
            cavity_stats[cavity]['total'] += 1
            if status == 'GOOD':
                cavity_stats[cavity]['passed'] += 1
            elif status == 'BAD':
                cavity_stats[cavity]['failed'] += 1
        
        # Calculate cavity success rates
        for cavity, stats in cavity_stats.items():
            success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            distribution['by_cavity'][cavity] = {
                **stats,
                'success_rate': success_rate,
                'performance_level': self._get_performance_level(success_rate)
            }
        
        return distribution
    
    def _identify_critical_issues(self, results: List[DimensionalResult]) -> List[Dict[str, Any]]:
        """Identify and prioritize critical quality issues"""
        critical_issues = []
        
        # Find failed dimensions with high out-of-spec counts
        for result in results:
            if self._get_status(result) == 'BAD':
                out_of_spec = getattr(result, 'out_of_spec_count', 0)
                severity = self._calculate_issue_severity(result, out_of_spec)
                
                if severity in ['Critical', 'High']:
                    critical_issues.append({
                        'element_id': result.element_id,
                        'description': result.description,
                        'cavity': getattr(result, 'cavity', 1),
                        'out_of_spec_count': out_of_spec,
                        'severity': severity,
                        'priority': self._calculate_priority(result),
                        'recommended_action': self._suggest_corrective_action(result)
                    })
        
        # Sort by priority (highest first)
        critical_issues.sort(key=lambda x: self._priority_value(x['priority']), reverse=True)
        
        return critical_issues[:10]  # Return top 10 critical issues
    
    def _analyze_quality_trends(self, results: List[DimensionalResult]) -> Dict[str, Any]:
        """Analyze quality trends and patterns"""
        # Store current results for trend analysis
        timestamp = datetime.now()
        current_quality = self._calculate_overall_quality(results)
        
        self.historical_data.append({
            'timestamp': timestamp,
            'quality_score': current_quality['score'],
            'total_dimensions': len(results),
            'success_rate': (current_quality['passed'] / len(results)) * 100 if results else 0
        })
        
        # Keep only last 20 data points
        if len(self.historical_data) > 20:
            self.historical_data = self.historical_data[-20:]
        
        # Analyze trends
        trends = {
            'direction': 'stable',
            'improvement_rate': 0.0,
            'volatility': 'low',
            'prediction': 'stable'
        }
        
        if len(self.historical_data) >= 3:
            recent_scores = [d['quality_score'] for d in self.historical_data[-3:]]
            
            # Determine trend direction
            if recent_scores[-1] > recent_scores[0] + 2:
                trends['direction'] = 'improving'
            elif recent_scores[-1] < recent_scores[0] - 2:
                trends['direction'] = 'declining'
            
            # Calculate improvement rate
            if len(recent_scores) >= 2:
                trends['improvement_rate'] = recent_scores[-1] - recent_scores[-2]
        
        return trends
    
    def _generate_quality_recommendations(self, results: List[DimensionalResult]) -> List[str]:
        """Generate specific quality improvement recommendations"""
        recommendations = []
        
        if not results:
            return ["📊 No data available for quality analysis"]
        
        quality_metrics = self._calculate_overall_quality(results)
        
        # Success rate recommendations
        if quality_metrics['score'] < 95:
            recommendations.append(
                f"🎯 Target improvement: Current quality at {quality_metrics['score']:.1f}% - "
                f"Focus on {quality_metrics['failed']} failed dimensions"
            )
        
        # Warning management
        if quality_metrics['warning'] > 0:
            recommendations.append(
                f"⚠️ Address {quality_metrics['warning']} warning conditions to prevent future failures"
            )
        
        # Cavity-specific recommendations
        cavity_analysis = self._analyze_quality_distribution(results)
        poor_cavities = [
            cavity for cavity, stats in cavity_analysis['by_cavity'].items()
            if stats['success_rate'] < 85
        ]
        
        if poor_cavities:
            recommendations.append(
                f"🏭 Prioritize cavity maintenance for: {', '.join(map(str, poor_cavities))}"
            )
        
        return recommendations
    
    def _calculate_efficiency_score(self, session_data: Dict[str, Any]) -> float:
        """Calculate overall efficiency score"""
        factors = []
        
        # Time efficiency
        avg_study_time = session_data.get('avg_study_time', 0)
        if avg_study_time > 0:
            time_efficiency = min(100, 300 / avg_study_time)  # Baseline 5 minutes
            factors.append(time_efficiency * 0.3)
        
        # Data completeness efficiency
        completeness = session_data.get('data_completeness', 0)
        factors.append(completeness * 0.3)
        
        # Quality efficiency
        success_rate = session_data.get('success_rate', 0)
        factors.append(success_rate * 0.4)
        
        return sum(factors) if factors else 0.0
    
    def _analyze_completeness(self, table_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data completeness comprehensively"""
        if table_data.empty:
            return {'overall_score': 0, 'details': {}}
        
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        completeness_details = {}
        
        total_cells = len(table_data) * len(measurement_cols)
        filled_cells = 0
        
        for col in measurement_cols:
            if col in table_data.columns:
                non_null = table_data[col].notna().sum()
                completeness_details[col] = {
                    'filled': non_null,
                    'total': len(table_data),
                    'percentage': (non_null / len(table_data)) * 100
                }
                filled_cells += non_null
        
        overall_score = (filled_cells / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            'overall_score': overall_score,
            'details': completeness_details,
            'filled_cells': filled_cells,
            'total_cells': total_cells,
            'completeness_grade': self._get_completeness_grade(overall_score)
        }
    
    def _analyze_consistency(self, table_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data consistency patterns"""
        if table_data.empty:
            return {'score': 0, 'issues': []}
        
        consistency_issues = []
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        
        # Check for unusual patterns
        for col in measurement_cols:
            if col in table_data.columns:
                data = table_data[col].dropna()
                if len(data) > 1:
                    # Check for extreme outliers
                    q1, q3 = data.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outliers = data[(data < lower_bound) | (data > upper_bound)]
                    if len(outliers) > 0:
                        consistency_issues.append(f"{col}: {len(outliers)} potential outliers detected")
        
        # Calculate consistency score
        base_score = 100
        penalty_per_issue = min(10, 100 / max(1, len(consistency_issues)))
        consistency_score = max(0, base_score - len(consistency_issues) * penalty_per_issue)
        
        return {
            'score': consistency_score,
            'issues': consistency_issues,
            'outlier_analysis': self._analyze_outliers(table_data)
        }
    
    def _analyze_accuracy(self, table_data: pd.DataFrame, original_data: Dict) -> Dict[str, Any]:
        """Analyze data accuracy through comparison with originals"""
        if table_data.empty or not original_data:
            return {'score': 100, 'modifications': 0}
        
        modifications = 0
        total_comparisons = 0
        
        # Compare current data with original
        for _, row in table_data.iterrows():
            element_id = row.get('element_id')
            if element_id in original_data:
                original = original_data[element_id]
                
                # Check measurements
                for i in range(1, 6):
                    orig_val = original.get('measurements', {}).get(f'measurement_{i}')
                    curr_val = row.get(f'measurement_{i}')
                    
                    if pd.notna(orig_val) and pd.notna(curr_val):
                        total_comparisons += 1
                        if abs(float(orig_val) - float(curr_val)) > 0.0001:
                            modifications += 1
        
        accuracy_score = 100
        if total_comparisons > 0:
            accuracy_score = max(0, 100 - (modifications / total_comparisons) * 100)
        
        return {
            'score': accuracy_score,
            'modifications': modifications,
            'total_comparisons': total_comparisons,
            'stability_rating': self._get_stability_rating(accuracy_score)
        }
    
    def _calculate_data_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        weights = {
            'completeness': 0.4,
            'consistency': 0.3,
            'accuracy': 0.3
        }
        
        completeness_score = analysis.get('completeness_analysis', {}).get('overall_score', 0)
        consistency_score = analysis.get('consistency_analysis', {}).get('score', 0)
        accuracy_score = analysis.get('accuracy_analysis', {}).get('score', 0)
        
        weighted_score = (
            completeness_score * weights['completeness'] +
            consistency_score * weights['consistency'] +
            accuracy_score * weights['accuracy']
        )
        
        return weighted_score
    
    # Helper methods
    def _get_status(self, result: DimensionalResult) -> str:
        """Get standardized result status"""
        return result.status.value if hasattr(result.status, 'value') else str(result.status)
    
    def _calculate_critical_penalty(self, results: List[DimensionalResult]) -> float:
        """Calculate penalty for critical failures"""
        critical_count = sum(
            1 for r in results 
            if getattr(r, 'out_of_spec_count', 0) >= 4
        )
        return (critical_count / len(results)) * 15 if results else 0  # 15% penalty per critical
    
    def _get_performance_level(self, success_rate: float) -> str:
        """Get performance level description"""
        if success_rate >= 95:
            return "Excellent"
        elif success_rate >= 90:
            return "Good"
        elif success_rate >= 80:
            return "Acceptable"
        elif success_rate >= 70:
            return "Poor"
        else:
            return "Critical"
    
    def _calculate_issue_severity(self, result: DimensionalResult, out_of_spec: int) -> str:
        """Calculate issue severity level"""
        if out_of_spec >= 4:
            return "Critical"
        elif out_of_spec >= 3:
            return "High"
        elif out_of_spec >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_priority(self, result: DimensionalResult) -> str:
        """Calculate issue priority"""
        out_of_spec = getattr(result, 'out_of_spec_count', 0)
        
        # High priority for critical dimensions
        if out_of_spec >= 4:
            return "Critical"
        elif out_of_spec >= 2:
            return "High"
        elif "critical" in str(result.description).lower():
            return "High"
        else:
            return "Medium"
    
    def _priority_value(self, priority: str) -> int:
        """Convert priority to numeric value for sorting"""
        priority_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        return priority_map.get(priority, 0)
    
    def _suggest_corrective_action(self, result: DimensionalResult) -> str:
        """Suggest corrective action for failed dimension"""
        out_of_spec = getattr(result, 'out_of_spec_count', 0)
        
        if out_of_spec >= 4:
            return "Immediate process halt and investigation required"
        elif out_of_spec >= 3:
            return "Review process parameters and tooling condition"
        elif out_of_spec >= 2:
            return "Monitor closely and adjust if trend continues"
        else:
            return "Standard monitoring and documentation"
    
    def _get_completeness_grade(self, score: float) -> str:
        """Get completeness grade"""
        if score >= 95:
            return "Excellent"
        elif score >= 85:
            return "Good"
        elif score >= 70:
            return "Fair"
        else:
            return "Poor"
    
    def _analyze_outliers(self, table_data: pd.DataFrame) -> Dict[str, Any]:
        """Detailed outlier analysis"""
        outlier_summary = {}
        measurement_cols = [f"measurement_{i}" for i in range(1, 6)]
        
        for col in measurement_cols:
            if col in table_data.columns:
                data = table_data[col].dropna()
                if len(data) > 3:  # Need minimum data for outlier detection
                    q1, q3 = data.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outliers = data[(data < lower_bound) | (data > upper_bound)]
                    outlier_summary[col] = {
                        'count': len(outliers),
                        'percentage': (len(outliers) / len(data)) * 100,
                        'severity': 'High' if len(outliers) > len(data) * 0.1 else 'Low'
                    }
        
        return outlier_summary
    
    def _get_stability_rating(self, accuracy_score: float) -> str:
        """Get data stability rating"""
        if accuracy_score >= 98:
            return "Very Stable"
        elif accuracy_score >= 95:
            return "Stable"
        elif accuracy_score >= 90:
            return "Moderately Stable"
        else:
            return "Unstable"
    
    def _generate_pattern_based_recommendations(self, 
                                               quality_data: Dict[str, Any],
                                               performance_data: Dict[str, Any], 
                                               integrity_data: Dict[str, Any]) -> List[str]:
        """Generate advanced pattern-based recommendations"""
        recommendations = []
        
        # Pattern 1: Cavity-specific issues
        cavity_dist = quality_data.get('quality_distribution', {}).get('by_cavity', {})
        poor_cavities = [
            str(cavity) for cavity, stats in cavity_dist.items()
            if stats.get('success_rate', 100) < 85
        ]
        
        if poor_cavities:
            recommendations.append(
                f"🔧 Investigate tooling/process for cavities: {', '.join(poor_cavities)}"
            )
        
        # Pattern 2: Data consistency issues
        consistency_score = integrity_data.get('consistency_analysis', {}).get('score', 100)
        if consistency_score < 85:
            recommendations.append(
                "📊 Data consistency issues detected - Review measurement procedures"
            )
        
        # Pattern 3: Efficiency optimization
        efficiency = performance_data.get('efficiency_score', 100)
        if efficiency < 80:
            recommendations.append(
                "⚡ Optimize workflow - Consider automation for repetitive tasks"
            )
        
        # Pattern 4: Trending issues
        trends = quality_data.get('quality_trends', {})
        if trends.get('direction') == 'declining':
            recommendations.append(
                "📉 Quality trend declining - Implement corrective measures immediately"
            )
        
        return recommendations
    
    def _analyze_throughput(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze throughput metrics"""
        return {
            'studies_per_hour': session_data.get('studies_run', 0) / max(1, session_data.get('session_hours', 1)),
            'dimensions_per_minute': session_data.get('total_dimensions', 0) / max(1, session_data.get('session_minutes', 1)),
            'efficiency_rating': 'Good'  # Placeholder for more complex calculation
        }
    
    def _analyze_resource_usage(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resource utilization"""
        return {
            'memory_efficiency': 85.0,  # Placeholder
            'processing_efficiency': 92.0,  # Placeholder
            'cache_hit_rate': session_data.get('cache_hit_rate', 0)
        }
    
    def _identify_optimization_opportunities(self, session_data: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Check cache efficiency
        cache_rate = session_data.get('cache_hit_rate', 0)
        if cache_rate < 70:
            opportunities.append("Improve caching strategy for better performance")
        
        # Check update frequency
        avg_update_time = session_data.get('avg_update_time', 0)
        if avg_update_time > 2.0:
            opportunities.append("Optimize update operations for faster response")
        
        return opportunities
    
    def _empty_quality_metrics(self) -> Dict[str, Any]:
        """Return empty quality metrics structure"""
        return {
            'overall_quality': {'score': 0.0, 'grade': 'N/A', 'status': 'No Data'},
            'quality_distribution': {'by_cavity': {}, 'by_evaluation_type': {}},
            'critical_issues': [],
            'quality_trends': {'direction': 'stable', 'improvement_rate': 0.0},
            'recommendations': ["📊 No data available for analysis"]
        }
    
    def _empty_integrity_metrics(self) -> Dict[str, Any]:
        """Return empty integrity metrics structure"""
        return {
            'completeness_analysis': {'overall_score': 0, 'details': {}},
            'consistency_analysis': {'score': 0, 'issues': []},
            'accuracy_analysis': {'score': 0, 'modifications': 0},
            'data_quality_score': 0.0,
            'integrity_issues': [],
            'improvement_suggestions': ["📋 Load data to begin integrity analysis"]
        }