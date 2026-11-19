from companion.service import main

if __name__ == "__main__":
    import sys
    if '--sdk-business' in sys.argv:
        from companion.business import main as business_main
        business_main()
    else:
        main()
