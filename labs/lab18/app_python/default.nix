{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    fastapi
    uvicorn
    prometheus-client
  ]);
in

pkgs.stdenv.mkDerivation {
  pname = "devops-info-service";
  version = "1.0.0";
  
  src = ./.;
  
  buildInputs = [ pythonEnv ];
  
  buildPhase = ''
    echo "Building DevOps Info Service..."
  '';
  
  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/lib
    mkdir -p $out/data
    cp -r . $out/lib/
    
    cat > $out/bin/devops-info-service << EOF
    #!${pythonEnv}/bin/python
    import sys
    import os
    sys.path.insert(0, "$out/lib")
    os.chdir("$out/lib")
    from app import app
    import uvicorn
    
    if __name__ == "__main__":
        port = int(os.environ.get('PORT', 8000))
        host = os.environ.get('HOST', '0.0.0.0')
        uvicorn.run(app, host=host, port=port)
    EOF
    
    chmod +x $out/bin/devops-info-service
  '';
  
  meta = {
    description = "DevOps Info Service with FastAPI";
    license = pkgs.lib.licenses.mit;
  };
}