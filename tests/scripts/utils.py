import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import os

def create_performance_charts(results_df: pd.DataFrame, output_dir: str):
    """
    Tạo các biểu đồ hiệu suất
    Args:
        results_df: DataFrame chứa kết quả test
        output_dir: Thư mục lưu biểu đồ
    """
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Biểu đồ thời gian phản hồi theo loại tìm kiếm
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='search_fields', y='response_time', data=results_df)
    plt.xticks(rotation=45)
    plt.title('Response Time by Search Type')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/response_time_by_search_type.png')
    plt.close()

    # 2. Biểu đồ số lượng kết quả tìm kiếm
    plt.figure(figsize=(12, 6))
    sns.barplot(x='search_fields', y='results_count', data=results_df)
    plt.xticks(rotation=45)
    plt.title('Results Count by Search Type')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/results_count_by_search_type.png')
    plt.close()

def calculate_statistics(results_df: pd.DataFrame) -> Dict:
    """
    Tính toán các thống kê từ kết quả test
    Args:
        results_df: DataFrame chứa kết quả test
    Returns:
        Dict chứa các thống kê
    """
    stats = {
        'total_searches': len(results_df),
        'successful_searches': len(results_df[results_df['status_code'] == 200]),
        'failed_searches': len(results_df[results_df['status_code'] != 200]),
        'avg_response_time': results_df['response_time'].mean(),
        'max_response_time': results_df['response_time'].max(),
        'min_response_time': results_df['response_time'].min(),
        'median_response_time': results_df['response_time'].median(),
        'success_rate': (results_df['status_code'] == 200).mean() * 100
    }

    # Thống kê theo loại tìm kiếm
    search_type_stats = results_df.groupby('search_fields').agg({
        'response_time': ['mean', 'max', 'min'],
        'results_count': 'mean',
        'status_code': lambda x: (x == 200).mean() * 100
    }).round(2)

    stats['search_type_stats'] = search_type_stats.to_dict()
    
    return stats

def format_excel_report(writer: pd.ExcelWriter, results_df: pd.DataFrame, stats: Dict):
    """
    Format báo cáo Excel
    Args:
        writer: ExcelWriter object
        results_df: DataFrame chứa kết quả test
        stats: Dict chứa các thống kê
    """
    # Tạo worksheet cho kết quả chi tiết
    results_df.to_excel(writer, sheet_name='Detailed Results', index=False)
    
    # Tạo worksheet cho thống kê
    stats_df = pd.DataFrame([stats])
    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
    
    # Tạo worksheet cho thống kê theo loại tìm kiếm
    search_type_stats = pd.DataFrame(stats['search_type_stats'])
    search_type_stats.to_excel(writer, sheet_name='Search Type Stats') 