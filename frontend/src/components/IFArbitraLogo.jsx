export default function IFArbitraLogo(){
    return(
        <div className="grid grid-cols-3 gap-[3px] mb-4">
            {[...Array(9)].map((_, i) => (
            <div
                key={i}
                className="w-[10px] h-[10px] bg-white rounded-[2px] opacity-90"
            />
            ))}
        </div>
    );
}