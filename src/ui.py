import sys

def print_progress(current: int, total: int, prefix: str = '', suffix: str = '', length: int = 50, fill: str = '#', print_end: str = "\r"):
    """
    Call in a loop to create terminal progress bar
    """
    if total == 0:
        return
        
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    # Print New Line on Complete
    if current == total: 
        print()

def print_summary(total_analyzed: int, language_counts: dict, added_counts: dict, unclassified_count: int, errors: list):
    """
    Prints the final execution summary.
    """
    print("\n" + "="*50)
    print("RESUMO DA OPERAÇÃO".center(50))
    print("="*50)
    
    print(f"\nTotal de músicas analisadas: {total_analyzed}")
    
    print("\nQuantidade por idioma:")
    for lang, count in sorted(language_counts.items(), key=lambda item: item[1], reverse=True):
        print(f"  - {lang}: {count}")
        
    print("\nQuantidade adicionada às playlists (novas músicas):")
    for lang, count in sorted(added_counts.items(), key=lambda item: item[1], reverse=True):
        if count > 0:
            print(f"  - Spotify — {lang}: {count}")
            
    if not any(count > 0 for count in added_counts.values()):
        print("  (Nenhuma música nova adicionada, todas as playlists já estavam atualizadas)")
        
    print(f"\nMúsicas não classificadas (Instrumental/Unknown): {unclassified_count}")
    
    if errors:
        print("\nErros encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nErros encontrados: 0")
        
    print("\n" + "="*50 + "\n")
